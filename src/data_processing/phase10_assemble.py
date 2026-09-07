"""
Phase 10 -- Unified Dataset Assembly
======================================
Merges all fully-processed per-dataset files (diffclass_*.csv) and the
attack transformation variants (transformed_attacks.csv) into three output files:

  data/processed/unified_dataset.csv
    - Master dataset: all samples from all sources, all fields included.
    - Deduplicated on sample_id. Includes original + transformed rows.

  data/processed/detector_dataset.csv
    - For binary / multi-class detection model training.
    - Columns: sample_id, prompt, label (binary), unified_label (multiclass),
               source, transformation, difficulty, prompt_length

  data/processed/assessment_dataset.csv
    - For the LLM attack assessment engine.
    - Malicious samples only (including transformations).
    - Columns: sample_id, prompt, unified_label, attack_subtype,
               attack_objective, severity, difficulty, transformation, source
"""

import sys
import io
import pathlib
import pandas as pd

# UTF-8 stdout
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR    = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT  = SCRIPT_DIR.parent.parent
INTERIM_DIR   = PROJECT_ROOT / "data" / "interim"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR   = PROJECT_ROOT / "reports"

def banner(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

# ── 1. Load per-dataset diffclass files ───────────────────────────────────────
DATASET_FILES = [
    "diffclass_harmbench.csv",
    "diffclass_jailbreakbench.csv",
    "diffclass_pibench.csv",
    "diffclass_tensor_trust.csv",
    "diffclass_benign.csv",
]

def load_datasets() -> pd.DataFrame:
    frames = []
    for fname in DATASET_FILES:
        path = INTERIM_DIR / fname
        if not path.exists():
            print(f"  [WARN] Missing: {fname}")
            continue
        df = pd.read_csv(path)
        frames.append(df)
        print(f"  Loaded {len(df):>5} rows from {fname}")
    return pd.concat(frames, ignore_index=True)


# ── 2. Load transformed attacks ───────────────────────────────────────────────
def load_transformed() -> pd.DataFrame:
    path = INTERIM_DIR / "transformed_attacks.csv"
    if not path.exists():
        print("  [WARN] transformed_attacks.csv not found -- skipping.")
        return pd.DataFrame()
    df = pd.read_csv(path)
    # Exclude rows with transformation=='original' since those are already
    # present in the diffclass files; only add the NEW variants
    df = df[df["transformation"] != "original"].copy()
    print(f"  Loaded {len(df):>5} transformed variant rows (non-original).")
    return df


def main():
    print(f"\n{'#'*60}")
    print(f"  PHASE 10 -- UNIFIED DATASET ASSEMBLY")
    print(f"{'#'*60}")

    # ── Step 1: Load base datasets
    banner("Loading base datasets")
    base_df = load_datasets()
    print(f"\n  Base dataset total: {len(base_df)} rows")

    # ── Step 2: Load transformation variants
    banner("Loading transformation variants")
    transform_df = load_transformed()

    # ── Step 3: Merge into unified dataset
    banner("Assembling unified_dataset.csv")
    if not transform_df.empty:
        # Align columns: fill any missing columns with None
        all_cols = list(dict.fromkeys(list(base_df.columns) + list(transform_df.columns)))
        for col in all_cols:
            if col not in base_df.columns:
                base_df[col] = None
            if col not in transform_df.columns:
                transform_df[col] = None
        unified = pd.concat([base_df, transform_df[all_cols]], ignore_index=True)
    else:
        unified = base_df.copy()

    # Ensure transformation column is filled for base rows (should be 'original')
    unified["transformation"] = unified["transformation"].fillna("original")

    # Drop exact duplicate sample_ids (keep first)
    before = len(unified)
    unified = unified.drop_duplicates(subset=["sample_id"], keep="first")
    print(f"  Dropped {before - len(unified)} duplicate sample_ids.")
    print(f"  Unified dataset: {len(unified)} rows")

    # Show label distribution
    print("\n  unified_label distribution:")
    for lbl, cnt in unified["unified_label"].value_counts().items():
        print(f"    {str(lbl):<35}: {cnt}")

    print("\n  transformation distribution:")
    for t, cnt in unified["transformation"].value_counts().items():
        print(f"    {str(t):<20}: {cnt}")

    unified_path = PROCESSED_DIR / "unified_dataset.csv"
    unified.to_csv(unified_path, index=False)
    print(f"\n  [+] Saved -> data/processed/unified_dataset.csv  ({len(unified)} rows)")

    # ── Step 4: detector_dataset.csv
    banner("Generating detector_dataset.csv")
    DETECTOR_COLS = [
        "sample_id", "prompt", "label", "unified_label",
        "source", "transformation", "difficulty", "prompt_length"
    ]
    # Ensure binary label column exists
    if "label" not in unified.columns:
        unified["label"] = unified["unified_label"].apply(
            lambda x: "benign" if x == "Benign" else "malicious"
        )
    # Only include rows where label is valid
    detector = unified[[c for c in DETECTOR_COLS if c in unified.columns]].copy()
    detector["label"] = detector["label"].fillna("malicious")
    detector = detector[detector["label"].isin(["benign", "malicious"])]
    
    detector_path = PROCESSED_DIR / "detector_dataset.csv"
    detector.to_csv(detector_path, index=False)
    print(f"  Rows: {len(detector)}")
    print(f"  Label distribution: {detector['label'].value_counts().to_dict()}")
    print(f"  [+] Saved -> data/processed/detector_dataset.csv")

    # ── Step 5: assessment_dataset.csv
    banner("Generating assessment_dataset.csv")
    ASSESSMENT_COLS = [
        "sample_id", "prompt", "unified_label", "attack_subtype",
        "attack_objective", "severity", "difficulty", "transformation", "source"
    ]
    # Only malicious samples for the assessment engine
    malicious_mask = unified["label"].isin(["malicious"]) | (
        ~unified["unified_label"].isin(["Benign", None, "nan", ""])
    )
    assessment = unified[unified["label"] == "malicious"].copy()
    assessment = assessment[[c for c in ASSESSMENT_COLS if c in assessment.columns]]
    
    assessment_path = PROCESSED_DIR / "assessment_dataset.csv"
    assessment.to_csv(assessment_path, index=False)
    print(f"  Rows: {len(assessment)}  (malicious only)")
    print(f"  unified_label distribution: {assessment['unified_label'].value_counts().to_dict()}")
    print(f"  transformation distribution: {assessment['transformation'].value_counts().to_dict()}")
    print(f"  [+] Saved -> data/processed/assessment_dataset.csv")

    print(f"\n{'#'*60}")
    print(f"  PHASE 10 COMPLETE [OK]")
    print(f"{'#'*60}\n")


if __name__ == "__main__":
    main()
