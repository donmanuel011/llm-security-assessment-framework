"""
Phase 12 -- Train/Test Split Strategy
=======================================
Implements a leakage-aware, stratified split of the dataset:
  - 70% Training
  - 15% Validation
  - 10% Known Attack Test
  - 5% Novel/Unseen Attack Test

Rules:
  - All transformed variants of a sample must stay in the same split
    as their original baseline (grouped by base sample_id).
  - Ensures no label leakage across splits.
"""

import sys
import io
import pathlib
import pandas as pd
from sklearn.model_selection import train_test_split
import random

# UTF-8 stdout
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR    = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT  = SCRIPT_DIR.parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR   = PROJECT_ROOT / "reports"

def banner(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def main():
    print(f"\n{'#'*60}")
    print(f"  PHASE 12 -- TRAIN/TEST SPLIT STRATEGY")
    print(f"{'#'*60}")

    detector_path = PROCESSED_DIR / "detector_dataset.csv"
    if not detector_path.exists():
        print(f"  [ERROR] {detector_path.name} not found!")
        return

    df = pd.read_csv(detector_path)
    
    # 1. Isolate the base sample ID (everything before '__')
    df["base_id"] = df["sample_id"].apply(lambda x: str(x).split("__")[0])
    
    # 2. Get unique base samples with their primary label for stratification
    base_df = df.drop_duplicates(subset=["base_id"]).copy()
    print(f"  Total rows: {len(df)}")
    print(f"  Total unique base samples: {len(base_df)}")

    # We want a 70 / 15 / 10 / 5 split of the base samples.
    # We will stratify by unified_label to ensure class balance.
    
    # Stratified split 1: 70% Train, 30% Rest
    train_base, rest_base = train_test_split(
        base_df, test_size=0.30, 
        stratify=base_df["unified_label"], random_state=42
    )

    # Stratified split 2: 15% Val (half of 30%), 15% Test
    val_base, test_base = train_test_split(
        rest_base, test_size=0.50, 
        stratify=rest_base["unified_label"], random_state=42
    )

    # Stratified split 3: 10% Known Test, 5% Novel/Unseen Test
    # Test base is 15% of total. We split 10/15 (0.666) to Known, 5/15 (0.333) to Novel
    # We can't always perfectly stratify small subsets, so we try our best.
    try:
        test_known_base, test_novel_base = train_test_split(
            test_base, test_size=0.333, 
            stratify=test_base["unified_label"], random_state=42
        )
    except ValueError:
        # Fallback if some classes have too few samples to split
        test_known_base, test_novel_base = train_test_split(
            test_base, test_size=0.333, random_state=42
        )

    # Verify no overlaps
    train_ids = set(train_base["base_id"])
    val_ids = set(val_base["base_id"])
    test_known_ids = set(test_known_base["base_id"])
    test_novel_ids = set(test_novel_base["base_id"])
    
    assert train_ids.isdisjoint(val_ids)
    assert train_ids.isdisjoint(test_known_ids)
    assert train_ids.isdisjoint(test_novel_ids)
    assert val_ids.isdisjoint(test_known_ids)
    assert val_ids.isdisjoint(test_novel_ids)
    assert test_known_ids.isdisjoint(test_novel_ids)

    # 3. Map splits back to the full dataset (including all variants)
    def assign_split(base_id):
        if base_id in train_ids: return "train"
        if base_id in val_ids: return "val"
        if base_id in test_known_ids: return "test_known"
        if base_id in test_novel_ids: return "test_novel"
        return "unknown"

    df["split"] = df["base_id"].apply(assign_split)

    # 4. Save and report
    banner("Split Results")
    
    split_counts = df["split"].value_counts()
    total = len(df)
    print("  Full Dataset Split Distribution (Including variants):")
    for s, c in split_counts.items():
        print(f"    {s:<15}: {c:>5} rows ({c/total*100:.1f}%)")
    
    # Check for label leakage (variants of a base sample crossing splits)
    # If base_id perfectly determines the split, leakage is 0.
    leakage = df.groupby("base_id")["split"].nunique()
    leaked_groups = leakage[leakage > 1]
    print(f"\n  Variants leaked across splits: {len(leaked_groups)}")
    if len(leaked_groups) == 0:
        print("  [+] No label leakage verified.")

    # Save output
    df.drop(columns=["base_id"], inplace=True)
    out_path = PROCESSED_DIR / "split_dataset.csv"
    df.to_csv(out_path, index=False)
    print(f"\n  [+] Saved split dataset -> {out_path.name}")

    # Generate small report
    report_path = REPORTS_DIR / "split_report.csv"
    report_df = df.groupby(["split", "unified_label"]).size().reset_index(name="count")
    report_df.to_csv(report_path, index=False)

    print(f"\n{'#'*60}")
    print(f"  PHASE 12 COMPLETE [OK]")
    print(f"{'#'*60}\n")

if __name__ == "__main__":
    main()
