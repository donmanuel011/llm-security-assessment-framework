"""
Phase 3 — Dataset Normalization
=================================
Converts raw datasets into a common schema.

Common schema:
  sample_id, prompt, label, attack_type, attack_subtype, source, language, 
  difficulty, prompt_length, attack_objective, obfuscation, transformation, 
  context_dependency, severity

Outputs interim files to: data/interim/
"""

import os, pathlib
import pandas as pd
import uuid

# ── paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
RAW_DIR      = PROJECT_ROOT / "data" / "raw"
INTERIM_DIR  = PROJECT_ROOT / "data" / "interim"
INTERIM_DIR.mkdir(parents=True, exist_ok=True)

COMMON_SCHEMA = [
    "sample_id", "prompt", "label", "attack_type", "attack_subtype", 
    "source", "language", "difficulty", "prompt_length", "attack_objective", 
    "obfuscation", "transformation", "context_dependency", "severity"
]

def banner(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def enforce_schema(df: pd.DataFrame) -> pd.DataFrame:
    for col in COMMON_SCHEMA:
        if col not in df.columns:
            df[col] = None
    
    # Compute prompt length automatically if missing
    df["prompt_length"] = df["prompt"].astype(str).str.len()
    
    return df[COMMON_SCHEMA]

def normalize_harmbench():
    banner("Normalizing HarmBench")
    df = pd.read_csv(RAW_DIR / "HarmBench" / "harmbench_behaviors_text_all.csv")
    
    out = pd.DataFrame()
    out["sample_id"] = "harmbench_" + df["BehaviorID"].astype(str)
    out["prompt"] = df["Behavior"]
    out["label"] = "malicious"
    out["attack_type"] = "Jailbreak"
    out["attack_subtype"] = df["SemanticCategory"]
    out["source"] = "HarmBench"
    out["language"] = "en"
    out["difficulty"] = None
    out["attack_objective"] = df["FunctionalCategory"]
    out["obfuscation"] = "none"
    out["transformation"] = "original"
    out["context_dependency"] = df["ContextString"].notna()
    out["severity"] = "high"
    
    out = enforce_schema(out)
    out_path = INTERIM_DIR / "norm_harmbench.csv"
    out.to_csv(out_path, index=False)
    print(f"  Saved {len(out)} rows -> {out_path.name}")


def normalize_pibench():
    banner("Normalizing PIBench")
    df = pd.read_json(RAW_DIR / "pibench" / "dataset" / "v1.0.0" / "full.jsonl", lines=True)
    
    out = pd.DataFrame()
    out["sample_id"] = "pibench_" + df["id"].astype(str)
    out["prompt"] = df["text"]
    out["label"] = df["label"].apply(lambda x: "malicious" if x == "injection" else "benign")
    
    def map_attack_type(row):
        if row["label"] == "benign":
            return "None"
        cat = str(row.get("category", "")).lower()
        if "indirect" in cat:
            return "Indirect Prompt Injection"
        elif "jailbreak" in cat:
            return "Jailbreak"
        elif "extraction" in cat:
            return "Prompt Leakage"
        return "Prompt Injection"

    out["attack_type"] = df.apply(map_attack_type, axis=1)
    out["attack_subtype"] = df["technique"]
    out["source"] = "PIBench"
    out["language"] = "en"
    out["difficulty"] = None
    out["attack_objective"] = None
    out["obfuscation"] = "none"
    out["transformation"] = "original"
    out["context_dependency"] = df["channel"] != "direct_user_input"
    out["severity"] = df["severity"]
    
    out = enforce_schema(out)
    out_path = INTERIM_DIR / "norm_pibench.csv"
    out.to_csv(out_path, index=False)
    print(f"  Saved {len(out)} rows -> {out_path.name}")


def normalize_tensor_trust():
    banner("Normalizing Tensor Trust")
    
    # Hijacking
    hij = pd.read_json(RAW_DIR / "tensor_trust" / "benchmarks" / "hijacking-robustness" / "v1" / "hijacking_robustness_dataset.jsonl", lines=True)
    out_hij = pd.DataFrame()
    out_hij["sample_id"] = "tt_hijack_" + hij["sample_id"].astype(str)
    out_hij["prompt"] = hij["attack"]
    out_hij["label"] = "malicious"
    out_hij["attack_type"] = "Prompt Injection"
    out_hij["attack_subtype"] = "hijacking"
    out_hij["source"] = "Tensor Trust"
    out_hij["language"] = "en"
    out_hij["difficulty"] = None
    out_hij["attack_objective"] = "access_code_bypass"
    out_hij["obfuscation"] = "none"
    out_hij["transformation"] = "original"
    out_hij["context_dependency"] = True
    out_hij["severity"] = "medium"

    # Extraction
    ext = pd.read_json(RAW_DIR / "tensor_trust" / "benchmarks" / "extraction-robustness" / "v1" / "extraction_robustness_dataset.jsonl", lines=True)
    out_ext = pd.DataFrame()
    out_ext["sample_id"] = "tt_extract_" + ext["sample_id"].astype(str)
    out_ext["prompt"] = ext["attack"]
    out_ext["label"] = "malicious"
    out_ext["attack_type"] = "Prompt Leakage"
    out_ext["attack_subtype"] = "extraction"
    out_ext["source"] = "Tensor Trust"
    out_ext["language"] = "en"
    out_ext["difficulty"] = None
    out_ext["attack_objective"] = "system_prompt_extraction"
    out_ext["obfuscation"] = "none"
    out_ext["transformation"] = "original"
    out_ext["context_dependency"] = True
    out_ext["severity"] = "medium"
    
    out = pd.concat([out_hij, out_ext], ignore_index=True)
    out = enforce_schema(out)
    
    out_path = INTERIM_DIR / "norm_tensor_trust.csv"
    out.to_csv(out_path, index=False)
    print(f"  Saved {len(out)} rows -> {out_path.name}")


def normalize_jailbreakbench():
    banner("Normalizing JailbreakBench")
    
    harm = pd.read_csv(RAW_DIR / "jailbreakbench" / "harmful-behaviors.csv")
    out_harm = pd.DataFrame()
    out_harm["sample_id"] = "jbb_harm_" + harm["Index"].astype(str)
    out_harm["prompt"] = harm["Goal"]
    out_harm["label"] = "malicious"
    out_harm["attack_type"] = "Jailbreak"
    out_harm["attack_subtype"] = harm["Category"]
    out_harm["source"] = "JailbreakBench"
    out_harm["language"] = "en"
    out_harm["difficulty"] = None
    out_harm["attack_objective"] = harm["Behavior"]
    out_harm["obfuscation"] = "none"
    out_harm["transformation"] = "original"
    out_harm["context_dependency"] = False
    out_harm["severity"] = "high"

    benign = pd.read_csv(RAW_DIR / "jailbreakbench" / "benign-behaviors.csv")
    out_benign = pd.DataFrame()
    out_benign["sample_id"] = "jbb_benign_" + benign["Index"].astype(str)
    out_benign["prompt"] = benign["Goal"]
    out_benign["label"] = "benign"
    out_benign["attack_type"] = "None"
    out_benign["attack_subtype"] = benign["Category"]
    out_benign["source"] = "JailbreakBench"
    out_benign["language"] = "en"
    out_benign["difficulty"] = None
    out_benign["attack_objective"] = None
    out_benign["obfuscation"] = "none"
    out_benign["transformation"] = "original"
    out_benign["context_dependency"] = False
    out_benign["severity"] = "none"
    
    out = pd.concat([out_harm, out_benign], ignore_index=True)
    out = enforce_schema(out)
    
    out_path = INTERIM_DIR / "norm_jailbreakbench.csv"
    out.to_csv(out_path, index=False)
    print(f"  Saved {len(out)} rows -> {out_path.name}")


def normalize_benign():
    banner("Normalizing Benign (Curated)")
    df = pd.read_json(RAW_DIR / "benign" / "benign_diverse.jsonl", lines=True)
    
    out = pd.DataFrame()
    out["sample_id"] = df["id"]
    out["prompt"] = df["text"]
    out["label"] = "benign"
    out["attack_type"] = "None"
    out["attack_subtype"] = df["category"]
    out["source"] = "curated_synthetic"
    out["language"] = df["language"]
    out["difficulty"] = None
    out["attack_objective"] = None
    out["obfuscation"] = "none"
    out["transformation"] = "original"
    out["context_dependency"] = False
    out["severity"] = "none"
    
    out = enforce_schema(out)
    
    out_path = INTERIM_DIR / "norm_benign.csv"
    out.to_csv(out_path, index=False)
    print(f"  Saved {len(out)} rows -> {out_path.name}")


def main():
    print(f"\n{'#'*60}")
    print(f"  PHASE 3 — DATASET NORMALIZATION")
    print(f"{'#'*60}")
    
    normalize_harmbench()
    normalize_pibench()
    normalize_tensor_trust()
    normalize_jailbreakbench()
    normalize_benign()
    
    print(f"\n{'#'*60}")
    print(f"  PHASE 3 COMPLETE [OK]")
    print(f"{'#'*60}\n")

if __name__ == "__main__":
    main()
