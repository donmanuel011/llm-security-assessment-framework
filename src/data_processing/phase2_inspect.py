"""
Phase 2 — Dataset Inspection
==============================
Runs inspection on all datasets:
  - HarmBench
  - PIBench
  - Tensor Trust
  - JailbreakBench
  - Benign (curated diverse)

Collects all metadata and generates reports/dataset_inventory.csv as required
by Phase 2 of the Tasklist.
"""

import sys, io, pathlib, json
import pandas as pd

# ── paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
REPORTS      = PROJECT_ROOT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

# Import the individual inspection modules
import inspect_harmbench
import inspect_pibench
import inspect_tensor_trust
import inspect_jailbreakbench

def banner(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def _extract_missing(d: dict) -> int:
    return sum(d.values()) if isinstance(d, dict) else 0

def inspect_benign(project_root: pathlib.Path) -> dict:
    """Inspect the benign dataset created in Phase 1."""
    ben_dir = project_root / "data" / "raw" / "benign"
    ben_f   = ben_dir / "benign_diverse.jsonl"
    
    if not ben_f.exists():
        return {}
        
    df = pd.read_json(ben_f, lines=True)
    
    return {
        "dataset": "Benign (Curated)",
        "n_total": len(df),
        "columns": list(df.columns),
        "label_values": ["benign"],
        "attack_categories": [],
        "missing_values": {c: int(df[c].isnull().sum()) for c in df.columns},
        "n_exact_duplicates": int(df.duplicated(subset=["text"]).sum()),
        "prompt_length_mean": round(float(df["text"].str.len().mean()), 1) if "text" in df.columns else 0.0,
        "language": "en",
        "source": "curated_synthetic"
    }

def main():
    banner("Phase 2 — Dataset Inspection Runner")
    
    print("Inspecting HarmBench...")
    hb_stats = inspect_harmbench.inspect(PROJECT_ROOT)
    
    print("Inspecting PIBench...")
    pb_stats = inspect_pibench.inspect(PROJECT_ROOT)
    
    print("Inspecting Tensor Trust...")
    tt_stats = inspect_tensor_trust.inspect(PROJECT_ROOT)
    
    print("Inspecting JailbreakBench...")
    jbb_stats = inspect_jailbreakbench.inspect(PROJECT_ROOT)
    
    print("Inspecting Benign (Curated)...")
    ben_stats = inspect_benign(PROJECT_ROOT)
    
    # ── Compile inventory data ────────────────────────────────────────────────
    
    inventory = []
    
    # 1. HarmBench
    inventory.append({
        "Dataset": "HarmBench",
        "Total Samples": hb_stats["n_total"],
        "Columns": ", ".join(hb_stats["columns"]),
        "Labels": ", ".join(hb_stats["label_values"]),
        "Attack Categories": ", ".join(hb_stats["attack_categories"]) if hb_stats.get("attack_categories") else "None",
        "Missing Values": _extract_missing(hb_stats["missing_values"]),
        "Exact Duplicates": hb_stats["n_exact_duplicates"],
        "Avg Prompt Length": hb_stats["prompt_length"]["mean"],
        "Language": hb_stats["language"],
        "Source": hb_stats["source_url"],
        "Metadata Fields": ", ".join(hb_stats["source_metadata"]) if hb_stats.get("source_metadata") else ""
    })
    
    # 2. PIBench
    inventory.append({
        "Dataset": "PIBench",
        "Total Samples": pb_stats["n_total"],
        "Columns": ", ".join(pb_stats["columns"]),
        "Labels": ", ".join(pb_stats["label_values"]),
        "Attack Categories": ", ".join(pb_stats["attack_categories"]) if pb_stats.get("attack_categories") else "None",
        "Missing Values": _extract_missing(pb_stats["missing_values"]),
        "Exact Duplicates": pb_stats["n_exact_duplicates"],
        "Avg Prompt Length": pb_stats["prompt_length_all"]["mean"],
        "Language": pb_stats["language"],
        "Source": pb_stats["source_url"],
        "Metadata Fields": ", ".join(pb_stats["source_metadata"]) if pb_stats.get("source_metadata") else ""
    })
    
    # 3. Tensor Trust - Hijacking
    hij = tt_stats["hijacking"]
    inventory.append({
        "Dataset": "Tensor Trust (Hijacking)",
        "Total Samples": hij["n_total"],
        "Columns": ", ".join(hij["columns"]),
        "Labels": hij["label"],
        "Attack Categories": "prompt_injection",
        "Missing Values": _extract_missing(hij["missing_values"]),
        "Exact Duplicates": hij["n_exact_duplicates"],
        "Avg Prompt Length": hij["attack_length"]["mean"],
        "Language": tt_stats["language"],
        "Source": tt_stats["source_url"],
        "Metadata Fields": "sample_id, pre_prompt, access_code, post_prompt"
    })
    
    # 4. Tensor Trust - Extraction
    ext = tt_stats["extraction"]
    inventory.append({
        "Dataset": "Tensor Trust (Extraction)",
        "Total Samples": ext["n_total"],
        "Columns": ", ".join(ext["columns"]),
        "Labels": ext["label"],
        "Attack Categories": "prompt_leakage",
        "Missing Values": _extract_missing(ext["missing_values"]),
        "Exact Duplicates": ext["n_exact_duplicates"],
        "Avg Prompt Length": ext["attack_length"]["mean"],
        "Language": tt_stats["language"],
        "Source": tt_stats["source_url"],
        "Metadata Fields": "sample_id, pre_prompt, post_prompt, access_code"
    })
    
    # 5. JailbreakBench
    inventory.append({
        "Dataset": "JailbreakBench",
        "Total Samples": jbb_stats["n_total"],
        "Columns": ", ".join(jbb_stats["columns"]),
        "Labels": ", ".join(jbb_stats["label_values"]),
        "Attack Categories": ", ".join(jbb_stats["attack_categories"]) if jbb_stats.get("attack_categories") else "None",
        "Missing Values": _extract_missing(jbb_stats["missing_harmful"]) + _extract_missing(jbb_stats["missing_benign"]),
        "Exact Duplicates": jbb_stats["n_within_harmful_dup"] + jbb_stats["n_within_benign_dup"] + jbb_stats["n_cross_file_dup"],
        "Avg Prompt Length": jbb_stats["prompt_length_all"]["mean"],
        "Language": jbb_stats["language"],
        "Source": jbb_stats["source_url"],
        "Metadata Fields": ", ".join(jbb_stats["source_metadata"]) if jbb_stats.get("source_metadata") else ""
    })
    
    # 6. Benign (Curated)
    if ben_stats:
        inventory.append({
            "Dataset": ben_stats["dataset"],
            "Total Samples": ben_stats["n_total"],
            "Columns": ", ".join(ben_stats["columns"]),
            "Labels": ", ".join(ben_stats["label_values"]),
            "Attack Categories": "None",
            "Missing Values": _extract_missing(ben_stats["missing_values"]),
            "Exact Duplicates": ben_stats["n_exact_duplicates"],
            "Avg Prompt Length": ben_stats["prompt_length_mean"],
            "Language": ben_stats["language"],
            "Source": ben_stats["source"],
            "Metadata Fields": "id, category, source, language, notes"
        })
        
    df_inv = pd.DataFrame(inventory)
    csv_path = REPORTS / "dataset_inventory.csv"
    df_inv.to_csv(csv_path, index=False)
    
    print(f"\nSuccessfully generated {csv_path}")
    print("\nInventory Summary:")
    print(df_inv[["Dataset", "Total Samples", "Avg Prompt Length"]].to_string())

if __name__ == "__main__":
    main()
