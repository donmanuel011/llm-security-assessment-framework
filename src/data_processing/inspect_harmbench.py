"""
inspect_harmbench.py
====================
Standalone inspection script for the HarmBench dataset.

Outputs a structured summary dict (returned by inspect()) and prints a
human-readable report to stdout. Run directly or imported by phase2_inspect.py.

Dataset location: data/raw/HarmBench/
Files:
  harmbench_behaviors_text_all.csv   – full set (400 rows)
  harmbench_behaviors_text_test.csv  – test split (320 rows)
  harmbench_behaviors_text_val.csv   – val split  (80 rows)

Schema:
  Behavior, FunctionalCategory, SemanticCategory, Tags, ContextString, BehaviorID
"""

import sys, io, pathlib, hashlib

import pandas as pd
import numpy  as np

# ── paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
HB_DIR       = PROJECT_ROOT / "data" / "raw" / "HarmBench"

# ── helpers ──────────────────────────────────────────────────────────────────
SEP  = "=" * 60
SEP2 = "-" * 60

def _pct(n, total): return f"{n}/{total} ({100*n/total:.1f}%)" if total else "0/0"
def _sha(path): return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════════
def inspect(project_root: pathlib.Path | None = None) -> dict:
    """Run full inspection and return structured summary dict."""
    root   = pathlib.Path(project_root) if project_root else PROJECT_ROOT
    hb_dir = root / "data" / "raw" / "HarmBench"

    files = {
        "all":  hb_dir / "harmbench_behaviors_text_all.csv",
        "test": hb_dir / "harmbench_behaviors_text_test.csv",
        "val":  hb_dir / "harmbench_behaviors_text_val.csv",
    }

    # ── load ──────────────────────────────────────────────────────────────────
    dfs = {k: pd.read_csv(v) for k, v in files.items()}
    df  = dfs["all"]

    prompt_col = "Behavior"          # the primary text we treat as 'prompt'
    func_col   = "FunctionalCategory"
    sem_col    = "SemanticCategory"

    # ── basic stats ───────────────────────────────────────────────────────────
    n_total      = len(df)
    columns      = list(df.columns)
    dtypes       = {c: str(t) for c, t in df.dtypes.items()}

    # ── missing values ────────────────────────────────────────────────────────
    missing = {c: int(df[c].isnull().sum()) for c in df.columns}

    # ── duplicates ────────────────────────────────────────────────────────────
    n_exact_dup  = int(df.duplicated(subset=[prompt_col]).sum())
    sha_series   = df[prompt_col].dropna().apply(
        lambda t: hashlib.sha256(t.strip().encode()).hexdigest()
    )
    n_sha_dup    = int(sha_series.duplicated().sum())

    # ── prompt length ─────────────────────────────────────────────────────────
    lengths = df[prompt_col].dropna().str.len()
    len_stats = {
        "min":    int(lengths.min()),
        "max":    int(lengths.max()),
        "mean":   round(float(lengths.mean()), 1),
        "median": round(float(lengths.median()), 1),
        "std":    round(float(lengths.std()), 1),
    }

    # ── label / category distributions ───────────────────────────────────────
    # HarmBench has no binary label — all rows are harmful behaviors.
    # Labels come from FunctionalCategory and SemanticCategory.
    func_dist = df[func_col].value_counts().to_dict()  if func_col in df.columns else {}
    sem_dist  = df[sem_col].value_counts().to_dict()   if sem_col  in df.columns else {}

    # Tags breakdown
    tags_present = df["Tags"].notna().sum() if "Tags" in df.columns else 0
    has_context  = df["ContextString"].notna().sum() if "ContextString" in df.columns else 0

    # Split sizes
    split_sizes = {k: len(v) for k, v in dfs.items()}

    # Language detection (all English — check for obvious non-ASCII)
    non_ascii = int((df[prompt_col].dropna()
                     .str.contains(r"[^\x00-\x7F]", regex=True)).sum())

    summary = {
        "dataset":            "HarmBench",
        "version":            "official (harmbench-behaviors-text v1)",
        "source_url":         "https://github.com/centerforaisafety/HarmBench",
        "local_dir":          str(hb_dir),
        "prompt_column":      prompt_col,
        "label_column":       None,          # no binary label; use category fields
        "label_values":       ["harmful"],   # all samples are harmful behaviors
        "language":           "en",
        "n_total":            n_total,
        "split_sizes":        split_sizes,
        "columns":            columns,
        "dtypes":             dtypes,
        "missing_values":     missing,
        "n_exact_duplicates": n_exact_dup,
        "n_sha256_duplicates":n_sha_dup,
        "prompt_length":      len_stats,
        "functional_categories": {k: int(v) for k, v in func_dist.items()},
        "semantic_categories":   {k: int(v) for k, v in sem_dist.items()},
        "n_with_tags":        int(tags_present),
        "n_with_context":     int(has_context),
        "n_non_ascii_prompts":non_ascii,
        "attack_categories":  list(sem_dist.keys()),
        "source_metadata":    ["BehaviorID", "Tags", "ContextString"],
    }
    return summary


# ═══════════════════════════════════════════════════════════════════════════════
def print_report(s: dict):
    print(f"\n{SEP}")
    print(f"  HARMBENCH — DATASET INSPECTION REPORT")
    print(f"{SEP}")
    print(f"  Version  : {s['version']}")
    print(f"  Source   : {s['source_url']}")
    print(f"  Dir      : {s['local_dir']}")
    print()

    print(f"[1] SAMPLE COUNTS")
    print(f"  Total      : {s['n_total']}")
    for split, n in s["split_sizes"].items():
        print(f"  {split:<8}   : {n}")
    print()

    print(f"[2] COLUMNS & DTYPES")
    for c, t in s["dtypes"].items():
        print(f"  {c:<25} {t}")
    print()

    print(f"[3] LABEL / CATEGORY DISTRIBUTION")
    print(f"  (All samples are harmful behaviors — no benign class)")
    print(f"  Functional categories:")
    for cat, n in s["functional_categories"].items():
        print(f"    {cat:<30} {n:>5}")
    print(f"  Semantic categories:")
    for cat, n in s["semantic_categories"].items():
        print(f"    {cat:<30} {n:>5}")
    print()

    print(f"[4] MISSING VALUES")
    for col, n in s["missing_values"].items():
        flag = "  <-- MISSING" if n > 0 else ""
        print(f"  {col:<25} {n:>5}{flag}")
    print()

    print(f"[5] DUPLICATE PROMPTS")
    print(f"  Exact duplicates     : {s['n_exact_duplicates']}")
    print(f"  SHA-256 duplicates   : {s['n_sha256_duplicates']}")
    print()

    print(f"[6] PROMPT LENGTH (chars)")
    for k, v in s["prompt_length"].items():
        print(f"  {k:<8} : {v}")
    print()

    print(f"[7] LANGUAGE & ENCODING")
    print(f"  Declared language    : {s['language']}")
    print(f"  Non-ASCII prompts    : {s['n_non_ascii_prompts']}")
    print()

    print(f"[8] SOURCE METADATA FIELDS")
    for f in s["source_metadata"]:
        print(f"  {f}")
    print(f"  Rows with Tags       : {s['n_with_tags']}")
    print(f"  Rows with Context    : {s['n_with_context']}")
    print(f"{SEP}\n")


# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    s = inspect()
    print_report(s)
