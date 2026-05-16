"""
Training Pipeline v3 — CMVD & Rickets Detection
================================================
Fixes in v3:
  • Skip corrupt / unreadable images gracefully (PIL.UnidentifiedImageError)
  • Fixed deprecated torch.cuda.amp → torch.amp (no more FutureWarnings)
  • Clear GPU/CPU detection message with install hint
  • num_workers=0 fallback on Windows to avoid DataLoader worker crashes
  • All original features kept:
      - Label smoothing, Mixup augmentation
      - Cosine LR with warm-up
      - Weighted sampler for class imbalance
      - AMP (mixed precision) on CUDA
      - TensorBoard-compatible history JSON
      - --mode 4class for CMVD multi-class training

Usage:
    python -m models.train --model cmvd    --data_dir ./data/cmvd    --epochs 60 --batch_size 32 --save_dir ./checkpoints
    python -m models.train --model rickets --data_dir ./data/rickets --epochs 60 --batch_size 16 --save_dir ./checkpoints
"""

import os
import sys
import argparse
import json
import time
import math
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, WeightedRandomSampler, Dataset
from torchvision import transforms
from torchvision.datasets import ImageFolder
from PIL import Image, UnidentifiedImageError
import numpy as np
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from models.cmvd_model import CMVDNet
from models.rickets_model import RicketsNet


# ─── Transforms ────────────────────────────────────────────────────────────────

TRAIN_TF = {
    "cmvd": transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomCrop(224),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.3, contrast=0.4),
        transforms.RandomAdjustSharpness(sharpness_factor=2, p=0.3),
        transforms.Grayscale(num_output_channels=3),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        transforms.RandomErasing(p=0.2, scale=(0.02, 0.08)),
    ]),
    "rickets": transforms.Compose([
        transforms.Resize((336, 336)),
        transforms.RandomCrop(300),
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(p=0.1),
        transforms.RandomRotation(20),
        transforms.ColorJitter(brightness=0.4, contrast=0.5),
        transforms.RandomAutocontrast(p=0.3),
        transforms.Grayscale(num_output_channels=3),
        transforms.ToTensor(),
        transforms.Normalize([0.449, 0.449, 0.449], [0.226, 0.226, 0.226]),
        transforms.RandomErasing(p=0.15, scale=(0.02, 0.1)),
    ]),
}

VAL_TF = {
    "cmvd": transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.Grayscale(num_output_channels=3),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ]),
    "rickets": transforms.Compose([
        transforms.Resize((300, 300)),
        transforms.Grayscale(num_output_channels=3),
        transforms.ToTensor(),
        transforms.Normalize([0.449, 0.449, 0.449], [0.226, 0.226, 0.226]),
    ]),
}


# ─── Safe Image Loader ─────────────────────────────────────────────────────────

def safe_pil_loader(path: str):
    """Load image safely — returns None if file is corrupt or unreadable."""
    try:
        with open(path, "rb") as f:
            img = Image.open(f)
            img.verify()          # catch truncated files
        # Re-open after verify (verify closes the file)
        with open(path, "rb") as f:
            img = Image.open(f)
            return img.convert("RGB")
    except (UnidentifiedImageError, OSError, Exception):
        return None


# ─── Dataset with corrupt-image skipping ──────────────────────────────────────

class MedDataset(Dataset):
    """
    Wraps ImageFolder and silently skips corrupt images.
    Falls back to a known-good image so DataLoader never crashes.
    """
    def __init__(self, root_dir: str, model_type: str, split: str = "train"):
        tf = (TRAIN_TF if split == "train" else VAL_TF)[model_type]

        # Use custom loader that won't crash on bad files
        base = ImageFolder(
            os.path.join(root_dir, split),
            transform=tf,
            loader=safe_pil_loader,
        )

        # Pre-filter: remove samples whose image can't be opened at all
        print(f"  Scanning {split} images for corrupt files...", end=" ", flush=True)
        valid_samples = []
        bad = 0
        for path, label in base.samples:
            img = safe_pil_loader(path)
            if img is not None:
                valid_samples.append((path, label))
            else:
                bad += 1
        print(f"OK  ({bad} corrupt files removed)")

        base.samples = valid_samples
        base.imgs    = valid_samples

        self.dataset = base
        self.classes = base.classes
        self.transform = tf

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, idx):
        # Extra safety: if loading still fails, return next valid item
        for attempt in range(idx, min(idx + 10, len(self.dataset))):
            try:
                return self.dataset[attempt]
            except Exception:
                continue
        # Last resort — return first item
        return self.dataset[0]

    def class_weights(self):
        targets = [lbl for _, lbl in self.dataset.samples]
        counts  = np.bincount(targets)
        w = 1.0 / counts
        return torch.FloatTensor(w / w.sum())


# ─── Mixup ─────────────────────────────────────────────────────────────────────

def mixup_data(x, y, alpha=0.4):
    lam = np.random.beta(alpha, alpha) if alpha > 0 else 1.0
    index  = torch.randperm(x.size(0), device=x.device)
    mixed  = lam * x + (1 - lam) * x[index]
    return mixed, y, y[index], lam


def mixup_criterion(criterion, pred, y_a, y_b, lam):
    return lam * criterion(pred, y_a) + (1 - lam) * criterion(pred, y_b)


# ─── Warmup + Cosine LR ────────────────────────────────────────────────────────

class WarmupCosineScheduler(optim.lr_scheduler._LRScheduler):
    def __init__(self, optimizer, warmup_epochs, total_epochs, eta_min=1e-6, last_epoch=-1):
        self.warmup_epochs = warmup_epochs
        self.total_epochs  = total_epochs
        self.eta_min       = eta_min
        super().__init__(optimizer, last_epoch)

    def get_lr(self):
        ep = self.last_epoch
        if ep < self.warmup_epochs:
            return [base * (ep + 1) / self.warmup_epochs for base in self.base_lrs]
        progress = (ep - self.warmup_epochs) / (self.total_epochs - self.warmup_epochs)
        cosine   = 0.5 * (1 + math.cos(math.pi * progress))
        return [self.eta_min + (base - self.eta_min) * cosine for base in self.base_lrs]


# ─── Trainer ───────────────────────────────────────────────────────────────────

class Trainer:
    def __init__(self, model, model_type, device, save_dir, num_classes,
                 use_mixup=True, label_smoothing=0.1):
        self.model           = model.to(device)
        self.model_type      = model_type
        self.device          = device
        self.save_dir        = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.num_classes     = num_classes
        self.use_mixup       = use_mixup
        self.label_smoothing = label_smoothing
        self.use_amp         = (device.type == "cuda")

        # ── Fixed: use torch.amp instead of deprecated torch.cuda.amp ──
        self.scaler = torch.amp.GradScaler("cuda", enabled=self.use_amp)

        self.history = {"train_loss": [], "val_loss": [], "val_acc": [], "val_auc": []}

    def _autocast(self):
        """Return the right autocast context for current device."""
        if self.use_amp:
            return torch.amp.autocast("cuda")
        return torch.amp.autocast("cpu", enabled=False)

    def train(self, train_loader, val_loader, epochs=60, lr=1e-4, class_weights=None):
        cw        = class_weights.to(self.device) if class_weights is not None else None
        criterion = nn.CrossEntropyLoss(weight=cw, label_smoothing=self.label_smoothing)
        optimizer = optim.AdamW(
            filter(lambda p: p.requires_grad, self.model.parameters()),
            lr=lr, weight_decay=1e-4,
        )
        scheduler = WarmupCosineScheduler(optimizer, warmup_epochs=5,
                                          total_epochs=epochs, eta_min=1e-6)

        best_auc, patience, stop_patience = 0.0, 0, 15

        print(f"\n{'='*60}")
        print(f"Training {self.model_type.upper()}  |  device={self.device}  |  epochs={epochs}")
        print(f"Mixup={self.use_mixup}  |  LabelSmoothing={self.label_smoothing}  |  AMP={self.use_amp}")
        print(f"{'='*60}\n")

        for epoch in range(epochs):
            t0         = time.time()
            train_loss = self._train_epoch(train_loader, criterion, optimizer)
            val_m      = self._val_epoch(val_loader, criterion)
            scheduler.step()

            self.history["train_loss"].append(train_loss)
            self.history["val_loss"].append(val_m["loss"])
            self.history["val_acc"].append(val_m["accuracy"])
            self.history["val_auc"].append(val_m["auc"])

            print(f"[{epoch+1:3d}/{epochs}] "
                  f"loss={train_loss:.4f}  val_loss={val_m['loss']:.4f}  "
                  f"acc={val_m['accuracy']:.1f}%  auc={val_m['auc']:.4f}  "
                  f"lr={scheduler.get_last_lr()[0]:.2e}  t={time.time()-t0:.1f}s")

            if val_m["auc"] > best_auc:
                best_auc = val_m["auc"]
                patience = 0
                torch.save(self.model.state_dict(),
                           self.save_dir / f"{self.model_type}_best.pth")
                print(f"  ✓ Best AUC: {best_auc:.4f}  → saved {self.model_type}_best.pth")
            else:
                patience += 1
                if patience >= stop_patience:
                    print(f"\nEarly stopping at epoch {epoch+1}")
                    break

        print(f"\nDone. Best AUC = {best_auc:.4f}")
        self._save_curves()
        with open(self.save_dir / f"{self.model_type}_history.json", "w") as f:
            json.dump(self.history, f, indent=2)

    def _density_target(self, labels):
        """
        Convert class labels to a soft bone-density target for RicketsNet's
        auxiliary density branch.
          Normal (2)         → density ≈ 0.85
          Mild_Rickets (0)   → density ≈ 0.50
          Severe_Rickets (1) → density ≈ 0.15
        Indices follow sorted class order: ['Mild_Rickets','Normal','Severe_Rickets']
        """
        mapping = {0: 0.50, 1: 0.15, 2: 0.85}   # Mild, Severe, Normal
        return torch.tensor(
            [mapping[l.item()] for l in labels],
            dtype=torch.float32, device=labels.device
        ).unsqueeze(1)

    def _train_epoch(self, loader, criterion, optimizer):
        self.model.train()
        total = 0.0
        density_criterion = nn.MSELoss() if self.model_type == "rickets" else None

        for imgs, labels in loader:
            imgs, labels = imgs.to(self.device), labels.to(self.device)
            optimizer.zero_grad()

            if self.use_mixup and self.model_type != "rickets":
                # Mixup only for CMVD (single-output model)
                imgs, la, lb, lam = mixup_data(imgs, labels, alpha=0.4)
                with self._autocast():
                    out  = self.model(imgs)
                    loss = mixup_criterion(criterion, out, la, lb, lam)
            elif self.model_type == "rickets":
                # RicketsNet: dual output (logits, density)
                with self._autocast():
                    out, density = self.model(imgs)
                    cls_loss     = criterion(out, labels)
                    den_loss     = density_criterion(density, self._density_target(labels))
                    loss         = cls_loss + 0.3 * den_loss   # weighted combined loss
            else:
                with self._autocast():
                    out  = self.model(imgs)
                    loss = criterion(out, labels)

            self.scaler.scale(loss).backward()
            self.scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            self.scaler.step(optimizer)
            self.scaler.update()
            total += loss.item()
        return total / len(loader)

    def _val_epoch(self, loader, criterion):
        self.model.eval()
        total, preds, labels_all, probs = 0.0, [], [], []
        density_criterion = nn.MSELoss() if self.model_type == "rickets" else None

        with torch.no_grad():
            for imgs, lbl in loader:
                imgs, lbl = imgs.to(self.device), lbl.to(self.device)
                with self._autocast():
                    if self.model_type == "rickets":
                        out, density = self.model(imgs)
                        den_loss     = density_criterion(density, self._density_target(lbl))
                        loss         = criterion(out, lbl) + 0.3 * den_loss
                    else:
                        out  = self.model(imgs)
                        loss = criterion(out, lbl)
                total += loss.item()
                p = torch.softmax(out, 1)
                preds.extend(torch.argmax(p, 1).cpu().numpy())
                labels_all.extend(lbl.cpu().numpy())
                probs.extend(p.cpu().numpy())

        preds      = np.array(preds)
        labels_all = np.array(labels_all)
        probs      = np.array(probs)
        acc = (preds == labels_all).mean() * 100
        try:
            if self.num_classes == 2:
                auc = roc_auc_score(labels_all, probs[:, 1])
            else:
                auc = roc_auc_score(labels_all, probs, multi_class="ovr", average="macro")
        except ValueError:
            auc = 0.5
        return {"loss": total / len(loader), "accuracy": acc, "auc": auc,
                "predictions": preds, "labels": labels_all}

    def _save_curves(self):
        fig, axes = plt.subplots(1, 3, figsize=(15, 4))
        axes[0].plot(self.history["train_loss"], label="Train", color="#e74c3c")
        axes[0].plot(self.history["val_loss"],   label="Val",   color="#3498db")
        axes[0].set_title(f"{self.model_type.upper()} Loss"); axes[0].legend(); axes[0].grid(alpha=0.3)
        axes[1].plot(self.history["val_acc"],  color="#2ecc71")
        axes[1].set_title("Validation Accuracy (%)"); axes[1].grid(alpha=0.3)
        axes[2].plot(self.history["val_auc"],  color="#9b59b6")
        axes[2].set_title("Val AUC-ROC"); axes[2].set_ylim([0, 1]); axes[2].grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(self.save_dir / f"{self.model_type}_curves.png", dpi=120)
        plt.close()
        print(f"  Training curves saved → {self.save_dir / f'{self.model_type}_curves.png'}")


# ─── Final Evaluation ──────────────────────────────────────────────────────────

def evaluate(model, loader, model_type, class_names, device):
    model.eval()
    preds, labels, probs = [], [], []
    with torch.no_grad():
        for imgs, lbl in loader:
            imgs = imgs.to(device)
            result = model(imgs)
            out    = result[0] if isinstance(result, (tuple, list)) else result
            p      = torch.softmax(out, 1)
            preds.extend(torch.argmax(p, 1).cpu().numpy())
            labels.extend(lbl.numpy())
            probs.extend(p.cpu().numpy())
    print("\n" + "="*60)
    print("FINAL EVALUATION REPORT")
    print("="*60)
    print(classification_report(labels, preds, target_names=class_names, digits=4))
    print("Confusion Matrix:")
    print(confusion_matrix(labels, preds))
    try:
        nc = len(class_names)
        auc = (roc_auc_score(labels, np.array(probs)[:, 1])
               if nc == 2
               else roc_auc_score(labels, probs, multi_class="ovr", average="macro"))
        print(f"\nAUC-ROC (macro): {auc:.4f}")
    except Exception as e:
        print(f"AUC calc failed: {e}")


# ─── GPU Check ─────────────────────────────────────────────────────────────────

def check_device(requested: str) -> torch.device:
    if requested != "auto":
        return torch.device(requested)

    if torch.cuda.is_available():
        dev  = torch.device("cuda")
        name = torch.cuda.get_device_name(0)
        mem  = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"Device: cuda  ({name}, {mem:.1f} GB VRAM)  ← GPU training ✓")
    else:
        dev = torch.device("cpu")
        print("Device: cpu  ← No NVIDIA GPU detected.")
        print("  Training on CPU will be VERY slow (hours per epoch).")
        print("  To enable GPU training:")
        print("  1. Check GPU: Run → nvidia-smi in terminal")
        print("  2. Install PyTorch with CUDA:")
        print("     pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118")
        print("  3. Or use Google Colab (free GPU): colab.research.google.com")
        print()
        resp = input("  Continue on CPU? (y/n): ").strip().lower()
        if resp != "y":
            print("Exiting. Please set up GPU and retry.")
            sys.exit(0)
    return dev


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model",      choices=["cmvd", "rickets"], required=True)
    parser.add_argument("--data_dir",   required=True)
    parser.add_argument("--epochs",     type=int,   default=60)
    parser.add_argument("--batch_size", type=int,   default=32)
    parser.add_argument("--lr",         type=float, default=3e-4)
    parser.add_argument("--save_dir",   default="./checkpoints")
    parser.add_argument("--device",     default="auto")
    parser.add_argument("--mode",       choices=["binary", "4class"], default="binary",
                        help="CMVD only: binary=2 classes, 4class=4 classes")
    parser.add_argument("--no_mixup",   action="store_true")
    args = parser.parse_args()

    device = check_device(args.device)

    # ── num_workers: 0 on Windows CPU to avoid multiprocessing issues ──
    nw = 0 if (device.type == "cpu" and os.name == "nt") else min(4, os.cpu_count() or 1)
    print(f"DataLoader workers: {nw}")

    print(f"\nLoading datasets from: {args.data_dir}")
    train_ds = MedDataset(args.data_dir, args.model, "train")
    val_ds   = MedDataset(args.data_dir, args.model, "val")
    print(f"Train: {len(train_ds)}  Val: {len(val_ds)}  Classes: {train_ds.classes}")

    cw = train_ds.class_weights()
    sw = [cw[lbl].item() for _, lbl in train_ds.dataset.samples]
    sampler = WeightedRandomSampler(sw, len(sw))

    train_loader = DataLoader(train_ds, batch_size=args.batch_size,
                              sampler=sampler, num_workers=nw,
                              pin_memory=(device.type == "cuda"))
    val_loader   = DataLoader(val_ds, batch_size=args.batch_size,
                              shuffle=False, num_workers=nw,
                              pin_memory=(device.type == "cuda"))

    if args.model == "cmvd":
        nc    = 4 if args.mode == "4class" else 2
        model = CMVDNet(num_classes=nc, pretrained=True)
    else:
        nc    = 3
        model = RicketsNet(num_classes=nc, pretrained=True)

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total     = sum(p.numel() for p in model.parameters())
    print(f"Parameters: {trainable:,} trainable / {total:,} total")

    trainer = Trainer(model, args.model, device, args.save_dir, nc,
                      use_mixup=not args.no_mixup)
    trainer.train(train_loader, val_loader, epochs=args.epochs,
                  lr=args.lr, class_weights=cw)

    print("\nRunning final evaluation on validation set...")
    evaluate(model, val_loader, args.model, train_ds.classes, device)


if __name__ == "__main__":
    main()