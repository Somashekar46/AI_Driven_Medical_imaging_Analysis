"""
Cloud GPU Training Script for Rickets Model
============================================
Works with Google Colab, AWS SageMaker, or Azure ML
Optimized for GPU acceleration with better augmentation and learning rates

Usage:
    # Local with GPU
    python train_rickets_cloud.py --epochs 100 --batch_size 32 --use_gpu

    # Upload dataset to cloud and run this script there
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

from models.rickets_model import RicketsNet


# ─────────────────────────────────────────────────────────────
# Transforms (optimized for GPU training)
# ─────────────────────────────────────────────────────────────

TRAIN_TF = transforms.Compose([
    transforms.Resize((336, 336)),
    transforms.RandomCrop(300),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomVerticalFlip(p=0.2),
    transforms.RandomRotation(25),
    transforms.ColorJitter(brightness=0.5, contrast=0.6, saturation=0.3),
    transforms.RandomAutocontrast(p=0.4),
    transforms.RandomAdjustSharpness(sharpness_factor=2, p=0.3),
    transforms.GaussianBlur(kernel_size=3, sigma=(0.1, 2.0)),
    transforms.Grayscale(num_output_channels=3),
    transforms.ToTensor(),
    transforms.Normalize([0.449, 0.449, 0.449], [0.226, 0.226, 0.226]),
    transforms.RandomErasing(p=0.2, scale=(0.02, 0.15)),
])

VAL_TF = transforms.Compose([
    transforms.Resize((300, 300)),
    transforms.Grayscale(num_output_channels=3),
    transforms.ToTensor(),
    transforms.Normalize([0.449, 0.449, 0.449], [0.226, 0.226, 0.226]),
])


# ─────────────────────────────────────────────────────────────
# Safe Image Loader
# ─────────────────────────────────────────────────────────────

def safe_pil_loader(path: str):
    """Load image safely — returns None if file is corrupt."""
    try:
        with open(path, "rb") as f:
            img = Image.open(f)
            img.verify()
        with open(path, "rb") as f:
            img = Image.open(f)
            return img.convert("RGB")
    except (UnidentifiedImageError, OSError, Exception):
        return None


# ─────────────────────────────────────────────────────────────
# Dataset with corrupt-image skipping
# ─────────────────────────────────────────────────────────────

class MedDataset(Dataset):
    """Wraps ImageFolder and skips corrupt images."""
    def __init__(self, root_dir: str, split: str = "train"):
        tf = (TRAIN_TF if split == "train" else VAL_TF)

        base = ImageFolder(
            os.path.join(root_dir, split),
            transform=tf,
            loader=safe_pil_loader,
        )

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
        base.imgs = valid_samples

        self.dataset = base
        self.classes = base.classes
        self.transform = tf

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, idx):
        for attempt in range(idx, min(idx + 10, len(self.dataset))):
            try:
                return self.dataset[attempt]
            except Exception:
                pass
        # Fallback: return first valid item
        return self.dataset[0]


# ─────────────────────────────────────────────────────────────
# Label Smoothing Loss
# ─────────────────────────────────────────────────────────────

class LabelSmoothingCrossEntropy(nn.Module):
    def __init__(self, num_classes, smoothing=0.1):
        super().__init__()
        self.smoothing = smoothing
        self.num_classes = num_classes

    def forward(self, logits, targets):
        log_probs = torch.nn.functional.log_softmax(logits, dim=1)
        
        # Create smoothed labels
        with torch.no_grad():
            true_dist = torch.zeros_like(log_probs)
            true_dist.fill_(self.smoothing / (self.num_classes - 1))
            true_dist.scatter_(1, targets.data.unsqueeze(1), 1.0 - self.smoothing)
        
        return torch.mean(torch.sum(-true_dist * log_probs, dim=1))


# ─────────────────────────────────────────────────────────────
# Training Loop
# ─────────────────────────────────────────────────────────────

def train_epoch(model, train_loader, optimizer, criterion, device, scaler=None):
    """Train for one epoch with AMP support."""
    model.train()
    total_loss = 0.0
    correct = 0
    total = 0

    for batch_idx, (images, targets) in enumerate(train_loader):
        images, targets = images.to(device), targets.to(device)

        optimizer.zero_grad()

        if scaler:  # With AMP
            with torch.autocast(device_type=device.type):
                logits, density = model(images)
                loss = criterion(logits, targets)
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimizer)
            scaler.update()
        else:  # Without AMP
            logits, density = model(images)
            loss = criterion(logits, targets)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

        total_loss += loss.item()
        _, predicted = logits.max(1)
        correct += predicted.eq(targets).sum().item()
        total += targets.size(0)

        if (batch_idx + 1) % 20 == 0:
            print(f"  [{batch_idx + 1}/{len(train_loader)}] Loss: {loss.item():.4f}")

    return total_loss / len(train_loader), 100.0 * correct / total


def validate(model, val_loader, criterion, device):
    """Validate model."""
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    all_preds = []
    all_targets = []

    with torch.no_grad():
        for images, targets in val_loader:
            images, targets = images.to(device), targets.to(device)
            logits, _ = model(images)
            loss = criterion(logits, targets)

            total_loss += loss.item()
            _, predicted = logits.max(1)
            correct += predicted.eq(targets).sum().item()
            total += targets.size(0)

            all_preds.extend(predicted.cpu().numpy())
            all_targets.extend(targets.cpu().numpy())

    accuracy = 100.0 * correct / total
    val_loss = total_loss / len(val_loader)
    
    try:
        auc = roc_auc_score(all_targets, all_preds, multi_class='ovr', average='weighted')
    except Exception:
        auc = 0.0

    return val_loss, accuracy, auc


# ─────────────────────────────────────────────────────────────
# Main Training
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Cloud GPU Training for Rickets Model")
    parser.add_argument("--data_dir", default="./data/rickets", help="Path to rickets data")
    parser.add_argument("--save_dir", default="./checkpoints", help="Checkpoint save directory")
    parser.add_argument("--epochs", type=int, default=100, help="Number of epochs")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")
    parser.add_argument("--use_gpu", action="store_true", help="Use GPU if available")
    args = parser.parse_args()

    # Setup device
    device = torch.device("cuda" if (args.use_gpu and torch.cuda.is_available()) else "cpu")
    print(f"\n{'='*70}")
    print(f"RICKETS MODEL TRAINING (Cloud GPU Optimized)")
    print(f"{'='*70}")
    print(f"Device: {device}")
    if device.type == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

    # Create checkpoints directory
    Path(args.save_dir).mkdir(exist_ok=True)

    # Load datasets
    print(f"\nLoading datasets from: {args.data_dir}")
    train_dataset = MedDataset(args.data_dir, split="train")
    val_dataset = MedDataset(args.data_dir, split="val")

    print(f"  Classes: {train_dataset.classes}")
    print(f"  Train samples: {len(train_dataset)}")
    print(f"  Val samples: {len(val_dataset)}")

    # Class weights for imbalanced data
    class_counts = np.bincount([train_dataset.dataset.targets[i] for i in range(len(train_dataset.dataset.samples))])
    class_weights = 1.0 / np.sqrt(class_counts)
    class_weights = class_weights / class_weights.sum() * len(class_weights)
    sample_weights = class_weights[train_dataset.dataset.targets]

    sampler = WeightedRandomSampler(sample_weights, len(sample_weights), replacement=True)

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, sampler=sampler, num_workers=0, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, num_workers=0, pin_memory=True)

    # Model, optimizer, loss
    model = RicketsNet(num_classes=3, pretrained=True).to(device)
    
    # Only unfreeze last layers for faster training
    for param in model.features.parameters():
        param.requires_grad = False
    for param in model.features[-1].parameters():
        param.requires_grad = True
    for param in model.cbam.parameters():
        param.requires_grad = True
    for param in model.density_branch.parameters():
        param.requires_grad = True
    for param in model.classifier.parameters():
        param.requires_grad = True

    optimizer = optim.AdamW([p for p in model.parameters() if p.requires_grad], 
                           lr=args.lr, weight_decay=1e-4)
    criterion = LabelSmoothingCrossEntropy(num_classes=3, smoothing=0.1)

    # LR scheduler with warmup
    warmup_epochs = 5
    def lr_lambda(epoch):
        if epoch < warmup_epochs:
            return (epoch + 1) / warmup_epochs
        return 0.5 * (1 + math.cos(math.pi * (epoch - warmup_epochs) / (args.epochs - warmup_epochs)))

    scheduler = optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)

    # AMP scaler if using CUDA
    scaler = torch.cuda.amp.GradScaler() if device.type == "cuda" else None

    # Training loop
    history = {"train_loss": [], "val_loss": [], "val_acc": [], "val_auc": []}
    best_auc = 0.0
    patience_counter = 0
    patience = 15

    print(f"\n{'='*70}")
    print(f"Starting training for {args.epochs} epochs...")
    print(f"{'='*70}\n")

    for epoch in range(args.epochs):
        print(f"Epoch [{epoch + 1}/{args.epochs}]")

        train_loss, train_acc = train_epoch(model, train_loader, optimizer, criterion, device, scaler)
        val_loss, val_acc, val_auc = validate(model, val_loader, criterion, device)

        scheduler.step()

        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)
        history["val_auc"].append(val_auc)

        print(f"  Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}%")
        print(f"  Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}% | Val AUC: {val_auc:.4f}\n")

        # Save best model
        if val_auc > best_auc:
            best_auc = val_auc
            patience_counter = 0
            checkpoint = {
                "epoch": epoch,
                "model": model.state_dict(),
                "optimizer": optimizer.state_dict(),
                "best_auc": best_auc,
            }
            save_path = os.path.join(args.save_dir, "rickets_best.pth")
            torch.save(checkpoint, save_path)
            print(f"✓ Saved best model to {save_path}\n")
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"Early stopping after {patience} epochs without improvement")
                break

    # Save final history
    history_path = os.path.join(args.save_dir, "rickets_history.json")
    with open(history_path, "w") as f:
        json.dump(history, f, indent=2)

    # Plot curves
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    
    axes[0].plot(history["train_loss"], label="Train Loss")
    axes[0].plot(history["val_loss"], label="Val Loss")
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Loss")
    axes[0].legend()
    axes[0].grid(True)
    
    axes[1].plot(history["val_acc"])
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("Accuracy (%)")
    axes[1].set_title("Validation Accuracy")
    axes[1].grid(True)
    
    axes[2].plot(history["val_auc"])
    axes[2].set_xlabel("Epoch")
    axes[2].set_ylabel("AUC Score")
    axes[2].set_title("Validation AUC")
    axes[2].grid(True)
    
    plt.tight_layout()
    plt.savefig(os.path.join(args.save_dir, "rickets_curves.png"), dpi=100, bbox_inches="tight")
    print(f"✓ Saved training curves to {args.save_dir}/rickets_curves.png")

    print(f"\n{'='*70}")
    print(f"Training completed!")
    print(f"Best Val AUC: {best_auc:.4f}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
