"""
Phase 7 — Taxonomy Mapping
===========================
Reads cross-deduplicated datasets (xdedup_*.csv) from data/interim/ and
maps raw attack_type / attack_subtype fields into the unified taxonomy:

  Unified taxonomy labels:
    - Benign
    - Prompt Injection
    - Indirect Prompt Injection
    - Jailbreak
    - Prompt Leakage

Outputs: data/interim/taxmap_*.csv
         reports/taxonomy_mapping_report.csv

Mapping rules per source:
  HarmBench:
    - All entries already tagged as Jailbreak (SemanticCategory is the subtype)
    - FunctionalCategory may suggest Prompt Leakage (e.g. "PII")

  PIBench:
    - label==benign           -> Benign
    - category contains "indirect" -> Indirect Prompt Injection
    - category contains "jailbreak" -> Jailbreak
    - category contains "extraction" -> Prompt Leakage
    - else                    -> Prompt Injection

  Tensor Trust:
    - attack_subtype=="hijacking"   -> Prompt Injection
    - attack_subtype=="extraction"  -> Prompt Leakage

  JailbreakBench:
    - label==benign  -> Benign
    - label==malicious -> Jailbreak

  Benign (curated synthetic):
    - All rows -> Benign
"""

import sys
import io
import os
import pathlib
import pandas as pd

# Force UTF-8 output
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR   = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
INTERIM_DIR  = PROJECT_ROOT / "data" / "interim"
REPORTS_DIR  = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Unified taxonomy labels ───────────────────────────────────────────────────
TAXONOMY_LABELS = [
    "Benign",
    "Prompt Injection",
    "Indirect Prompt Injection",
    "Jailbreak",
    "Prompt Leakage",
]

def banner(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ── Per-dataset mapping functions ─────────────────────────────────────────────

def map_harmbench(df: pd.DataFrame) -> pd.DataFrame:
    """
    HarmBench: all entries are malicious.
    attack_type is already 'Jailbreak'. 
    FunctionalCategory hints may refine to Prompt Leakage.
    """
    def _map(row):
        if str(row.get("label", "")).lower() == "benign":
            return "Benign"
        obj = str(row.get("attack_objective", "")).lower()
        # Specific FunctionalCategory values that indicate leakage
        if any(k in obj for k in ["pii", "privacy", "personal info", "leak", "extract"]):
            return "Prompt Leakage"
        return "Jailbreak"

    df["unified_label"] = df.apply(_map, axis=1)
    return df


def map_pibench(df: pd.DataFrame) -> pd.DataFrame:
    """
    PIBench: attack_type was already mapped in Phase 3 normalization.
    We re-derive from attack_type to ensure consistency.
    """
    mapping = {
        "None":                      "Benign",
        "Prompt Injection":          "Prompt Injection",
        "Indirect Prompt Injection": "Indirect Prompt Injection",
        "Jailbreak":                 "Jailbreak",
        "Prompt Leakage":            "Prompt Leakage",
    }

    def _map(row):
        if str(row.get("label", "")).lower() == "benign":
            return "Benign"
        attack_t = str(row.get("attack_type", "")).strip()
        return mapping.get(attack_t, "Prompt Injection")

    df["unified_label"] = df.apply(_map, axis=1)
    return df


def map_tensor_trust(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tensor Trust: 
      attack_subtype == "hijacking"  -> Prompt Injection
      attack_subtype == "extraction" -> Prompt Leakage
    """
    def _map(row):
        subtype = str(row.get("attack_subtype", "")).lower()
        if "extract" in subtype:
            return "Prompt Leakage"
        if "hijack" in subtype or "injection" in subtype:
            return "Prompt Injection"
        return "Prompt Injection"  # safe default for Tensor Trust

    df["unified_label"] = df.apply(_map, axis=1)
    return df


def map_jailbreakbench(df: pd.DataFrame) -> pd.DataFrame:
    """
    JailbreakBench:
      label == benign   -> Benign
      label == malicious -> Jailbreak
    """
    def _map(row):
        if str(row.get("label", "")).lower() == "benign":
            return "Benign"
        return "Jailbreak"

    df["unified_label"] = df.apply(_map, axis=1)
    return df


def map_benign(df: pd.DataFrame) -> pd.DataFrame:
    """
    Curated benign dataset: all rows are Benign.
    """
    df["unified_label"] = "Benign"
    return df


# ── Dataset config ────────────────────────────────────────────────────────────

DATASET_CONFIG = [
    ("HarmBench",      "xdedup_harmbench.csv",      map_harmbench),
    ("JailbreakBench", "xdedup_jailbreakbench.csv", map_jailbreakbench),
    ("PIBench",        "xdedup_pibench.csv",         map_pibench),
    ("TensorTrust",    "xdedup_tensor_trust.csv",    map_tensor_trust),
    ("Benign",         "xdedup_benign.csv",           map_benign),
]


def process_dataset(name: str, fname: str, map_fn) -> dict:
    input_path = INTERIM_DIR / fname
    if not input_path.exists():
        print(f"  [WARN] Missing: {fname} -- skipping.")
        return {}

    df = pd.read_csv(input_path)
    print(f"  Loaded {len(df)} rows from {fname}")

    df = map_fn(df)

    # Update attack_type column to mirror unified_label for consistency
    df["attack_type"] = df["unified_label"]

    dist = df["unified_label"].value_counts().to_dict()
    print(f"  Unified label distribution: {dist}")

    # Validate all labels are in the taxonomy
    unknown = df[~df["unified_label"].isin(TAXONOMY_LABELS)]
    if not unknown.empty:
        print(f"  [WARN] {len(unknown)} rows have unrecognized labels!")
        print(f"  Unknown labels: {unknown['unified_label'].unique()}")

    out_fname = fname.replace("xdedup_", "taxmap_")
    out_path = INTERIM_DIR / out_fname
    df.to_csv(out_path, index=False)
    print(f"  [+] Saved {len(df)} rows -> {out_fname}")

    return {"dataset": name, **{lbl: dist.get(lbl, 0) for lbl in TAXONOMY_LABELS}, "total": len(df)}


def main():
    print(f"\n{'#'*60}")
    print(f"  PHASE 7 -- TAXONOMY MAPPING")
    print(f"{'#'*60}")

    print("\nUnified taxonomy labels:")
    for lbl in TAXONOMY_LABELS:
        print(f"    - {lbl}")

    report_rows = []

    for name, fname, map_fn in DATASET_CONFIG:
        banner(f"Mapping {name}")
        row = process_dataset(name, fname, map_fn)
        if row:
            report_rows.append(row)

    # Summary report
    report_df = pd.DataFrame(report_rows)
    report_path = REPORTS_DIR / "taxonomy_mapping_report.csv"
    report_df.to_csv(report_path, index=False)
    print(f"\n  [+] Taxonomy mapping report saved -> {report_path}")

    # Print overall distribution
    print("\n  Overall unified label distribution across all datasets:")
    for lbl in TAXONOMY_LABELS:
        total = report_df[lbl].sum() if lbl in report_df.columns else 0
        print(f"    {lbl:<30}: {total}")

    print(f"\n{'#'*60}")
    print(f"  PHASE 7 COMPLETE [OK]")
    print(f"{'#'*60}\n")


if __name__ == "__main__":
    main()
