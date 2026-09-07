"""
Phase 4 — Data Cleaning
=======================
Reads normalized datasets from data/interim/ and applies text cleaning 
while preserving adversarial characteristics (capitalization, special chars, spacing).

Outputs cleaned files to: data/interim/clean_*.csv
"""

import os
import pathlib
import pandas as pd
import unicodedata
import ftfy

# ── paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
INTERIM_DIR  = PROJECT_ROOT / "data" / "interim"

def banner(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def clean_text_adversarial_aware(text: str) -> str:
    """
    Cleans text while strictly preserving adversarial features:
    - Retains original capitalization (NO .lower())
    - Retains special characters (NO regex stripping)
    - Retains internal spacing/tabs/newlines (NO re.sub(r'\\s+', ' ', text))
    - Fixes encoding issues using ftfy
    - Applies standard Unicode NFC normalization
    - Strips ONLY leading/trailing whitespace
    """
    if pd.isna(text) or not isinstance(text, str):
        return ""
    
    # Fix bad encoding / mojibake (e.g., â€™ -> ')
    text = ftfy.fix_text(text)
    
    # Unicode normalization (NFC is generally safe for security tasks)
    text = unicodedata.normalize('NFC', text)
    
    # Strip leading/trailing whitespaces only, preserve internal deliberate spacing
    text = text.strip()
    
    return text

def process_dataset(filename: str):
    input_path = INTERIM_DIR / filename
    if not input_path.exists():
        print(f"  [WARN] File not found: {input_path.name}")
        return
    
    df = pd.read_csv(input_path)
    initial_len = len(df)
    print(f"  Loaded {initial_len} rows from {filename}")
    
    # 1. Missing Value Handling
    # Handle NULL and whitespace-only prompts
    df['prompt'] = df['prompt'].fillna('')
    df = df[df['prompt'].str.strip() != '']
    removed_empty = initial_len - len(df)
    if removed_empty > 0:
        print(f"  [-] Removed {removed_empty} rows with empty or whitespace-only prompts.")
    
    # Handle missing labels
    if 'label' in df.columns:
        valid_labels = ['benign', 'malicious']
        invalid_mask = ~df['label'].isin(valid_labels)
        if invalid_mask.sum() > 0:
            print(f"  [WARN] Found {invalid_mask.sum()} invalid labels. Mapping to 'unknown'.")
            df.loc[invalid_mask, 'label'] = 'unknown'
    
    # Handle missing attack category fields
    if 'attack_type' in df.columns:
        df['attack_type'] = df['attack_type'].fillna('Unknown')
    if 'attack_subtype' in df.columns:
        df['attack_subtype'] = df['attack_subtype'].fillna('Unknown')
    
    # 2. Text Normalization
    df['prompt'] = df['prompt'].apply(clean_text_adversarial_aware)
    
    # Remove any prompts that became empty after strict cleaning
    curr_len = len(df)
    df = df[df['prompt'] != '']
    removed_post_clean = curr_len - len(df)
    if removed_post_clean > 0:
        print(f"  [-] Removed {removed_post_clean} rows that became empty post-normalization.")

    # Recompute length
    df["prompt_length"] = df["prompt"].astype(str).str.len()
    
    out_filename = filename.replace("norm_", "clean_")
    out_path = INTERIM_DIR / out_filename
    df.to_csv(out_path, index=False)
    print(f"  [+] Saved {len(df)} cleaned rows -> {out_filename}")


def main():
    print(f"\n{'#'*60}")
    print(f"  PHASE 4 — DATA CLEANING")
    print(f"{'#'*60}")
    
    datasets = [
        "norm_harmbench.csv",
        "norm_pibench.csv",
        "norm_tensor_trust.csv",
        "norm_jailbreakbench.csv",
        "norm_benign.csv"
    ]
    
    for ds in datasets:
        banner(f"Processing {ds}")
        process_dataset(ds)

    print(f"\n{'#'*60}")
    print(f"  PHASE 4 COMPLETE [OK]")
    print(f"{'#'*60}\n")

if __name__ == "__main__":
    main()
