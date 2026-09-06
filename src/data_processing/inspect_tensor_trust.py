"""
inspect_tensor_trust.py
=======================
Standalone inspection script for the Tensor Trust dataset.

Outputs a structured summary dict (returned by inspect()) and prints a
human-readable report to stdout.

Dataset location: data/raw/tensor_trust/
Benchmarks used:
  benchmarks/hijacking-robustness/v1/hijacking_robustness_dataset.jsonl
    → 776 samples | Schema: sample_id, pre_prompt, access_code, post_prompt, attack
    → "attack" column = the adversarial injection payload (label: prompt_injection)

  benchmarks/extraction-robustness/v1/extraction_robustness_dataset.jsonl
    → 570 samples | Same schema
    → "attack" column = the extraction attempt (label: prompt_leakage)

Notes:
  - No binary benign/malicious label; ALL samples are attacks.
  - The "attack" field is the prompt we classify.
  - pre_prompt / post_prompt represent the defended system prompt (context).
"""

import sys, io, pathlib, hashlib

import pandas as pd

# ── paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
TT_DIR       = PROJECT_ROOT / "data" / "raw" / "tensor_trust"

SEP = "=" * 60


# ═══════════════════════════════════════════════════════════════════════════════
def _inspect_file(fpath: pathlib.Path, label: str) -> dict:
    """Inspect a single JSONL benchmark file."""
    df = pd.read_json(fpath, lines=True)

    prompt_col = "attack"   # the adversarial text we care about

    n_total  = len(df)
    columns  = list(df.columns)
    dtypes   = {c: str(t) for c, t in df.dtypes.items()}
    missing  = {c: int(df[c].isnull().sum()) for c in df.columns}

    # Duplicates on the attack column
    n_exact_dup = int(df.duplicated(subset=[prompt_col]).sum())
    sha_series  = df[prompt_col].dropna().apply(
        lambda t: hashlib.sha256(str(t).strip().encode()).hexdigest()
    )
    n_sha_dup   = int(sha_series.duplicated().sum())

    # Prompt length (attack field)
    lengths = df[prompt_col].dropna().str.len()
    len_stats = {
        "min":    int(lengths.min()),
        "max":    int(lengths.max()),
        "mean":   round(float(lengths.mean()), 1),
        "median": round(float(lengths.median()), 1),
        "std":    round(float(lengths.std()), 1),
    }

    # Pre-prompt (system prompt / defense) length
    pre_lengths = df["pre_prompt"].dropna().str.len() if "pre_prompt" in df.columns else pd.Series(dtype=float)
    pre_len_stats = {
        "mean": round(float(pre_lengths.mean()), 1) if not pre_lengths.empty else 0,
        "max":  int(pre_lengths.max()) if not pre_lengths.empty else 0,
    }

    # Attack length buckets (useful for difficulty classification later)
    buckets = {
        "short  (<100 chars)":  int((lengths < 100).sum()),
        "medium (100-500)":     int(((lengths >= 100) & (lengths < 500)).sum()),
        "long   (500-2000)":    int(((lengths >= 500) & (lengths < 2000)).sum()),
        "very_long (>=2000)":   int((lengths >= 2000).sum()),
    }

    # Non-ASCII detection (encoding/obfuscation attacks)
    non_ascii = int(
        df[prompt_col].dropna().str.contains(r"[^\x00-\x7F]", regex=True).sum()
    )

    sha256 = hashlib.sha256(fpath.read_bytes()).hexdigest()

    return {
        "file":                str(fpath.name),
        "label":               label,
        "n_total":             n_total,
        "columns":             columns,
        "dtypes":              dtypes,
        "prompt_column":       prompt_col,
        "missing_values":      missing,
        "n_exact_duplicates":  n_exact_dup,
        "n_sha256_duplicates": n_sha_dup,
        "attack_length":       len_stats,
        "attack_length_buckets": buckets,
        "pre_prompt_length":   pre_len_stats,
        "n_non_ascii_attacks": non_ascii,
        "sha256":              sha256,
    }


# ═══════════════════════════════════════════════════════════════════════════════
def inspect(project_root: pathlib.Path | None = None) -> dict:
    root   = pathlib.Path(project_root) if project_root else PROJECT_ROOT
    tt_dir = root / "data" / "raw" / "tensor_trust"

    hij_f = tt_dir / "benchmarks" / "hijacking-robustness"  / "v1" / "hijacking_robustness_dataset.jsonl"
    ext_f = tt_dir / "benchmarks" / "extraction-robustness" / "v1" / "extraction_robustness_dataset.jsonl"

    hij = _inspect_file(hij_f, label="prompt_injection")
    ext = _inspect_file(ext_f, label="prompt_leakage")

    # Combined view
    n_combined  = hij["n_total"] + ext["n_total"]
    sha_combined = hashlib.sha256(
        (hij["sha256"] + ext["sha256"]).encode()
    ).hexdigest()[:16]

    summary = {
        "dataset":          "Tensor Trust",
        "version":          "benchmarks v1 / raw data v2",
        "source_url":       "https://tensortrust.ai/paper",
        "paper":            "https://arxiv.org/abs/2311.09384",
        "local_dir":        str(tt_dir),
        "prompt_column":    "attack",
        "label_column":     None,    # assigned by benchmark: hijacking=PI, extraction=PL
        "label_values":     ["prompt_injection", "prompt_leakage"],
        "language":         "en",
        "n_combined":       n_combined,
        "hijacking":        hij,
        "extraction":       ext,
        "recommended_use": {
            "hijacking":  "label=prompt_injection   | use attack col as prompt",
            "extraction": "label=prompt_leakage     | use attack col as prompt",
            "training_split":    "70% of each benchmark",
            "evaluation_split":  "30% of each benchmark (reserved for known-test set)",
        },
        "attack_categories": {
            "prompt_injection": hij["n_total"],
            "prompt_leakage":   ext["n_total"],
        },
    }
    return summary


# ═══════════════════════════════════════════════════════════════════════════════
def print_report(s: dict):
    def _sub(title, sub):
        print(f"  -- {title} --")
        print(f"  File             : {sub['file']}")
        print(f"  Label            : {sub['label']}")
        print(f"  Total samples    : {sub['n_total']}")
        print(f"  Columns          : {sub['columns']}")
        print()
        print(f"  Missing values:")
        for col, n in sub["missing_values"].items():
            flag = "  <-- MISSING" if n > 0 else ""
            print(f"    {col:<25} {n:>5}{flag}")
        print()
        print(f"  Exact duplicates   : {sub['n_exact_duplicates']}")
        print(f"  SHA-256 duplicates : {sub['n_sha256_duplicates']}")
        print()
        print(f"  Attack length (chars):")
        for k, v in sub["attack_length"].items():
            print(f"    {k:<8} : {v}")
        print(f"  Attack length buckets:")
        for bkt, n in sub["attack_length_buckets"].items():
            print(f"    {bkt:<25} {n:>5}")
        print(f"  Pre-prompt mean len : {sub['pre_prompt_length']['mean']}")
        print(f"  Non-ASCII attacks   : {sub['n_non_ascii_attacks']}")
        print()

    print(f"\n{SEP}")
    print(f"  TENSOR TRUST — DATASET INSPECTION REPORT")
    print(f"{SEP}")
    print(f"  Version    : {s['version']}")
    print(f"  Source     : {s['source_url']}")
    print(f"  Combined N : {s['n_combined']}")
    print()

    print(f"[1] HIJACKING-ROBUSTNESS BENCHMARK")
    _sub("Prompt Injection attacks", s["hijacking"])

    print(f"[2] EXTRACTION-ROBUSTNESS BENCHMARK")
    _sub("Prompt Leakage attacks", s["extraction"])

    print(f"[3] RECOMMENDED USE")
    for k, v in s["recommended_use"].items():
        print(f"  {k:<20} : {v}")
    print(f"{SEP}\n")


# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    s = inspect()
    print_report(s)
