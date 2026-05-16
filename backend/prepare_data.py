"""
Data Preparation Pipeline — CMVD & Rickets Detection
=====================================================
Converts raw datasets into train/val folder structure for train.py.

Usage:
    # Prepare CMVD only
    python prepare_data.py --dataset cmvd --src H:\\medical-ai\\medical-ai\\Dataset\\CMVD --dst H:\\medical-ai\\medical-ai\\backend\\data

    # Prepare Rickets only
    python prepare_data.py --dataset rickets --src H:\\medical-ai\\medical-ai\\Dataset\\Rickets --dst H:\\medical-ai\\medical-ai\\backend\\data

    # Prepare BOTH at once
    python prepare_data.py --dataset both --cmvd_src H:\\medical-ai\\medical-ai\\Dataset\\CMVD --rickets_src H:\\medical-ai\\medical-ai\\Dataset\\Rickets --dst H:\\medical-ai\\medical-ai\\backend\\data

CMVD label mapping:
    "Normal Person ECG Images"                          → Normal
    "ECG Images of Myocardial Infarction Patients"      → CMVD
    "ECG Images of Patient that have abnormal heartbeat"→ CMVD
    "ECG Images of Patient that have History of MI"     → CMVD

Rickets label mapping (from dataset.csv):
    osteopenia == '1'              → Severe_Rickets  (2,465 images)
    fracture_visible == '1' only   → Mild_Rickets    (11,040 images)
    neither                        → Normal           (6,285 images)
"""

import os
import sys
import shutil
import argparse
import csv
import random
from pathlib import Path
from collections import defaultdict


# ─────────────────────────────────────────────────────────────
# CMVD Preparation
# ─────────────────────────────────────────────────────────────

CMVD_FOLDER_MAP = {
    "Normal Person":         "Normal",
    "Myocardial Infarction": "CMVD",
    "abnormal heartbeat":    "CMVD",
    "History of MI":         "CMVD",
}


def prepare_cmvd(src_dir: Path, dst_dir: Path, val_split: float = 0.2, seed: int = 42):
    print(f"\n{'='*60}")
    print("CMVD Dataset Preparation")
    print(f"Source : {src_dir}")
    print(f"Output : {dst_dir}")
    print(f"{'='*60}")

    if not src_dir.exists():
        print(f"ERROR: Source directory not found: {src_dir}")
        sys.exit(1)

    supported = {".jpg", ".jpeg", ".png", ".bmp"}
    class_files: dict = defaultdict(list)

    for folder in src_dir.iterdir():
        if not folder.is_dir():
            continue
        label = None
        for key, cls in CMVD_FOLDER_MAP.items():
            if key.lower() in folder.name.lower():
                label = cls
                break
        if label is None:
            print(f"  [SKIP] Unknown folder: {folder.name}")
            continue
        images = [f for f in folder.iterdir() if f.suffix.lower() in supported]
        print(f"  [MAP] '{folder.name}' → {label}  ({len(images)} images)")
        class_files[label].extend(images)

    if not class_files:
        print("ERROR: No images found. Check the source path.")
        sys.exit(1)

    print(f"\n  Label distribution:")
    for cls, files in sorted(class_files.items()):
        print(f"    {cls:<20}: {len(files):>5} images")

    _split_and_copy(class_files, dst_dir, val_split, seed)
    _print_summary(dst_dir)


# ─────────────────────────────────────────────────────────────
# Rickets Preparation  ← FIXED for images_part1–4 structure
# ─────────────────────────────────────────────────────────────

def prepare_rickets(src_dir: Path, dst_dir: Path, val_split: float = 0.2, seed: int = 42):
    print(f"\n{'='*60}")
    print("Rickets Dataset Preparation")
    print(f"Source : {src_dir}")
    print(f"Output : {dst_dir}")
    print(f"{'='*60}")

    if not src_dir.exists():
        print(f"ERROR: Source directory not found: {src_dir}")
        sys.exit(1)

    # ── Find dataset.csv ──────────────────────────────────────
    csv_path = src_dir / "dataset.csv"
    if not csv_path.exists():
        print(f"ERROR: dataset.csv not found at {csv_path}")
        print("  Please copy dataset.csv into your Rickets folder:")
        print(f"  copy dataset.csv \"{src_dir}\\dataset.csv\"")
        sys.exit(1)
    print(f"  CSV found: {csv_path}")

    # ── Find all images across images_part1, images_part2, images_part3, images_part4 ──
    supported = {".png", ".jpg", ".jpeg", ".bmp"}
    img_map: dict = {}  # filestem → Path

    # Search in images_part* folders (your actual structure)
    part_dirs = sorted([d for d in src_dir.iterdir()
                        if d.is_dir() and d.name.lower().startswith("images_part")])

    # Also check other common structures as fallback
    fallback_dirs = [
        src_dir / "supervisely" / "wrist" / "img",
        src_dir / "yolov5" / "images",
        src_dir / "images",
        src_dir,  # images directly in root
    ]

    search_dirs = part_dirs if part_dirs else [d for d in fallback_dirs if d.exists()]

    if not search_dirs:
        print(f"ERROR: No image directories found in {src_dir}")
        sys.exit(1)

    print(f"\n  Searching for images in:")
    for d in search_dirs:
        count = 0
        for f in d.iterdir():
            if f.is_file() and f.suffix.lower() in supported:
                img_map[f.stem] = f
                count += 1
        print(f"    {d.name:<20} → {count} images found")

    print(f"\n  Total unique images found: {len(img_map)}")

    if len(img_map) == 0:
        print("ERROR: No images found in any folder.")
        print("  Make sure your images are in images_part1, images_part2, etc.")
        sys.exit(1)

    # ── Parse CSV and assign labels ───────────────────────────
    class_files: dict = defaultdict(list)
    missing      = 0
    uncertain    = 0
    matched      = 0

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip uncertain diagnoses
            if row.get("diagnosis_uncertain", "").strip() == "1":
                uncertain += 1
                continue

            stem     = row["filestem"].strip()
            img_path = img_map.get(stem)

            if img_path is None:
                missing += 1
                continue

            osteopenia = row.get("osteopenia",       "").strip()
            fracture   = row.get("fracture_visible", "").strip()

            if osteopenia == "1":
                label = "Severe_Rickets"
            elif fracture == "1":
                label = "Mild_Rickets"
            else:
                label = "Normal"

            class_files[label].append(img_path)
            matched += 1

    print(f"\n  CSV parsing results:")
    print(f"    Matched to images    : {matched}")
    print(f"    Skipped (uncertain)  : {uncertain}")
    print(f"    Missing images       : {missing}")

    print(f"\n  Label distribution (before balancing):")
    for cls, files in sorted(class_files.items()):
        print(f"    {cls:<22}: {len(files):>6} images")

    if not class_files:
        print("\nERROR: No images could be matched to CSV entries.")
        print("  Check that filestem values in CSV match your image filenames (without extension).")
        _show_sample_debug(img_map, csv_path)
        sys.exit(1)

    # ── Balance classes ───────────────────────────────────────
    # Cap to prevent huge Normal/Mild imbalance vs Severe
    # Keep all Severe_Rickets (smallest class), cap others at 3×
    random.seed(seed)
    minority = min(len(v) for v in class_files.values())
    cap = max(minority * 3, 2000)

    print(f"\n  Balancing (cap = {cap} per class):")
    for cls in list(class_files.keys()):
        original = len(class_files[cls])
        if original > cap:
            class_files[cls] = random.sample(class_files[cls], cap)
            print(f"    {cls:<22}: {original} → {cap} (capped)")
        else:
            print(f"    {cls:<22}: {original} (kept all)")

    _split_and_copy(class_files, dst_dir, val_split, seed)
    _print_summary(dst_dir)


def _show_sample_debug(img_map: dict, csv_path: Path):
    """Show sample stems from both sides to help debug mismatches."""
    img_stems = list(img_map.keys())[:5]
    print(f"\n  Sample image stems found on disk:")
    for s in img_stems:
        print(f"    {s}")

    print(f"\n  Sample filestem values from CSV:")
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= 5:
                break
            print(f"    {row['filestem'].strip()}")


# ─────────────────────────────────────────────────────────────
# Shared Utilities
# ─────────────────────────────────────────────────────────────

def _sanitize_filename(name: str) -> str:
    """Remove or replace characters that are invalid in Windows filenames."""
    import re
    # Replace invalid Windows filename characters with underscore
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')
    # If somehow empty, use fallback
    if not sanitized:
        sanitized = "image"
    return sanitized


def _split_and_copy(class_files: dict, dst_dir: Path, val_split: float, seed: int):
    """Split each class into train/val and copy files, skipping bad files gracefully."""
    random.seed(seed)
    total_copied = 0
    total_skipped = 0

    for cls, files in sorted(class_files.items()):
        random.shuffle(files)
        n_val = max(1, int(len(files) * val_split))
        splits = {
            "val":   files[:n_val],
            "train": files[n_val:],
        }
        for split, split_files in splits.items():
            out_dir = dst_dir / split / cls
            out_dir.mkdir(parents=True, exist_ok=True)

            for src_path in split_files:
                # Sanitize destination filename to avoid Windows invalid char errors
                safe_name  = _sanitize_filename(src_path.stem) + src_path.suffix.lower()
                dst_path   = out_dir / safe_name

                # Make unique if collision after sanitizing
                counter = 1
                while dst_path.exists():
                    # Check if it's the same source file (already copied)
                    if dst_path.stat().st_size == src_path.stat().st_size:
                        break
                    safe_name = f"{_sanitize_filename(src_path.stem)}_{counter}{src_path.suffix.lower()}"
                    dst_path  = out_dir / safe_name
                    counter  += 1
                else:
                    try:
                        shutil.copy2(src_path, dst_path)
                        total_copied += 1
                    except (OSError, PermissionError) as e:
                        total_skipped += 1
                        if total_skipped <= 5:
                            print(f"  [WARN] Skipping '{src_path.name}': {e}")
                        elif total_skipped == 6:
                            print(f"  [WARN] (further skip warnings suppressed...)")
                    continue
                total_copied += 1  # already existed / same size

    print(f"\n  Files copied : {total_copied}")
    if total_skipped:
        print(f"  Files skipped: {total_skipped} (bad filenames / permission errors)")


def _print_summary(dst_dir: Path):
    """Print final train/val counts per class."""
    print(f"\n  Final dataset at: {dst_dir}")
    for split in ["train", "val"]:
        split_dir = dst_dir / split
        if not split_dir.exists():
            continue
        print(f"\n  [{split.upper()}]")
        total = 0
        for cls_dir in sorted(split_dir.iterdir()):
            if cls_dir.is_dir():
                n = len(list(cls_dir.iterdir()))
                total += n
                print(f"    {cls_dir.name:<25}: {n:>5} images")
        print(f"    {'TOTAL':<25}: {total:>5} images")


# ─────────────────────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Prepare CMVD and Rickets datasets for training",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--dataset",
                        choices=["cmvd", "rickets", "both"],
                        required=True,
                        help="Which dataset to prepare")
    parser.add_argument("--src",
                        type=str,
                        help="Source directory (for single dataset mode)")
    parser.add_argument("--cmvd_src",
                        type=str,
                        help="CMVD source directory (for --dataset both)")
    parser.add_argument("--rickets_src",
                        type=str,
                        help="Rickets source directory (for --dataset both)")
    parser.add_argument("--dst",
                        type=str,
                        default="./data",
                        help="Output root directory (default: ./data)")
    parser.add_argument("--val_split",
                        type=float,
                        default=0.2,
                        help="Validation split ratio (default: 0.2 = 20%%)")
    parser.add_argument("--seed",
                        type=int,
                        default=42,
                        help="Random seed for reproducibility")
    args = parser.parse_args()

    dst = Path(args.dst)

    if args.dataset == "cmvd":
        if not args.src:
            parser.error("--src is required for --dataset cmvd")
        prepare_cmvd(Path(args.src), dst / "cmvd", args.val_split, args.seed)

    elif args.dataset == "rickets":
        if not args.src:
            parser.error("--src is required for --dataset rickets")
        prepare_rickets(Path(args.src), dst / "rickets", args.val_split, args.seed)

    elif args.dataset == "both":
        if not args.cmvd_src or not args.rickets_src:
            parser.error("--cmvd_src and --rickets_src are both required for --dataset both")
        prepare_cmvd(
            Path(args.cmvd_src),
            dst / "cmvd",
            args.val_split,
            args.seed,
        )
        prepare_rickets(
            Path(args.rickets_src),
            dst / "rickets",
            args.val_split,
            args.seed,
        )

    print("\n" + "="*60)
    print("Data preparation complete!")
    print("="*60)
    print("\nNext — train your models:")
    print(f"\n  CMVD:")
    print(f"  python models/train.py --model cmvd --data_dir {dst / 'cmvd'} --epochs 60 --batch_size 32 --save_dir ./checkpoints")
    print(f"\n  Rickets:")
    print(f"  python models/train.py --model rickets --data_dir {dst / 'rickets'} --epochs 60 --batch_size 16 --save_dir ./checkpoints")


if __name__ == "__main__":
    main()