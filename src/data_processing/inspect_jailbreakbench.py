"""
inspect_jailbreakbench.py
=========================
Standalone inspection script for the JailbreakBench (JBB-Behaviors) dataset.

Outputs a structured summary dict (returned by inspect()) and prints a
human-readable report to stdout.

Dataset location: data/raw/jailbreakbench/
Files:
  harmful-behaviors.csv  – 100 harmful jailbreak behaviors
  benign-behaviors.csv   – 100 benign behaviors
  judge-comparison.csv   – judge evaluation records (not a primary behavior file)

Schema (harmful + benign CSVs):
  Index, Goal, Target, Behavior, Category, Source

Label: "harmful" | "benign"  (derived from which file the row came from)
"""

import sys, io, pathlib, hashlib

import pandas as pd

# ── paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
JBB_DIR      = PROJECT_ROOT / "data" / "raw" / "jailbreakbench"

SEP = "=" * 60


# ═══════════════════════════════════════════════════════════════════════════════
def inspect(project_root: pathlib.Path | None = None) -> dict:
    root    = pathlib.Path(project_root) if project_root else PROJECT_ROOT
    jbb_dir = root / "data" / "raw" / "jailbreakbench"

    harm_f  = jbb_dir / "harmful-behaviors.csv"
    ben_f   = jbb_dir / "benign-behaviors.csv"
    judge_f = jbb_dir / "judge-comparison.csv"

    harm_df = pd.read_csv(harm_f)
    ben_df  = pd.read_csv(ben_f)

    # Add derived label column
    harm_df["label"] = "harmful"
    ben_df["label"]  = "benign"

    full_df = pd.concat([harm_df, ben_df], ignore_index=True)

    prompt_col = "Goal"        # the primary behavior/prompt text
    label_col  = "label"
    cat_col    = "Category"

    # ── basic ─────────────────────────────────────────────────────────────────
    n_total  = len(full_df)
    n_harm   = len(harm_df)
    n_ben    = len(ben_df)
    columns  = list(harm_df.columns)  # original columns (before label addition)
    dtypes   = {c: str(t) for c, t in harm_df.dtypes.items()}

    # ── label distribution ────────────────────────────────────────────────────
    label_dist = full_df[label_col].value_counts().to_dict()

    # ── attack categories ─────────────────────────────────────────────────────
    harm_cat_dist = harm_df[cat_col].value_counts().to_dict() if cat_col in harm_df.columns else {}
    ben_cat_dist  = ben_df[cat_col].value_counts().to_dict()  if cat_col in ben_df.columns  else {}
    all_cat_dist  = full_df[cat_col].value_counts().to_dict() if cat_col in full_df.columns else {}

    # Source distribution
    src_dist  = full_df["Source"].value_counts().to_dict() if "Source" in full_df.columns else {}

    # ── missing values ────────────────────────────────────────────────────────
    missing_harm = {c: int(harm_df[c].isnull().sum()) for c in harm_df.columns}
    missing_ben  = {c: int(ben_df[c].isnull().sum())  for c in ben_df.columns}

    # ── duplicates ────────────────────────────────────────────────────────────
    # Within harmful set
    n_harm_dup = int(harm_df.duplicated(subset=[prompt_col]).sum())
    # Within benign set
    n_ben_dup  = int(ben_df.duplicated(subset=[prompt_col]).sum())
    # Cross-file duplicates (same Goal text in both)
    n_cross_dup = int(full_df.duplicated(subset=[prompt_col]).sum())

    sha_series = full_df[prompt_col].dropna().apply(
        lambda t: hashlib.sha256(str(t).strip().encode()).hexdigest()
    )
    n_sha_dup  = int(sha_series.duplicated().sum())

    # ── prompt length (Goal column) ───────────────────────────────────────────
    def len_stats(series):
        s = series.dropna().str.len()
        return {
            "min":    int(s.min()),
            "max":    int(s.max()),
            "mean":   round(float(s.mean()), 1),
            "median": round(float(s.median()), 1),
            "std":    round(float(s.std()), 1),
        }

    all_len    = len_stats(full_df[prompt_col])
    harm_len   = len_stats(harm_df[prompt_col])
    ben_len    = len_stats(ben_df[prompt_col])

    # ── non-ASCII ─────────────────────────────────────────────────────────────
    non_ascii = int(
        full_df[prompt_col].dropna().str.contains(r"[^\x00-\x7F]", regex=True).sum()
    )

    # ── judge-comparison.csv basic info ───────────────────────────────────────
    judge_info = {}
    if judge_f.exists():
        jdf = pd.read_csv(judge_f)
        judge_info = {
            "n_rows":   len(jdf),
            "columns":  list(jdf.columns),
            "sha256":   hashlib.sha256(judge_f.read_bytes()).hexdigest(),
        }

    summary = {
        "dataset":              "JailbreakBench",
        "version":              "JBB-Behaviors v1.0",
        "source_url":           "https://huggingface.co/datasets/JailbreakBench/JBB-Behaviors",
        "paper":                "https://arxiv.org/abs/2404.01318",
        "local_dir":            str(jbb_dir),
        "prompt_column":        prompt_col,
        "label_column":         label_col,
        "label_values":         ["harmful", "benign"],
        "language":             "en",
        "n_total":              n_total,
        "n_harmful":            n_harm,
        "n_benign":             n_ben,
        "columns":              columns,
        "dtypes":               dtypes,
        "label_distribution":   {k: int(v) for k, v in label_dist.items()},
        "harmful_categories":   {k: int(v) for k, v in harm_cat_dist.items()},
        "benign_categories":    {k: int(v) for k, v in ben_cat_dist.items()},
        "all_categories":       {k: int(v) for k, v in all_cat_dist.items()},
        "source_distribution":  {k: int(v) for k, v in src_dist.items()},
        "missing_harmful":      missing_harm,
        "missing_benign":       missing_ben,
        "n_within_harmful_dup": n_harm_dup,
        "n_within_benign_dup":  n_ben_dup,
        "n_cross_file_dup":     n_cross_dup,
        "n_sha256_duplicates":  n_sha_dup,
        "prompt_length_all":    all_len,
        "prompt_length_harmful":harm_len,
        "prompt_length_benign": ben_len,
        "n_non_ascii_prompts":  non_ascii,
        "judge_comparison":     judge_info,
        "attack_categories":    list(harm_cat_dist.keys()),
        "source_metadata":      ["Index", "Target", "Category", "Source"],
        "sha256_harmful":       hashlib.sha256(harm_f.read_bytes()).hexdigest(),
        "sha256_benign":        hashlib.sha256(ben_f.read_bytes()).hexdigest(),
    }
    return summary


# ═══════════════════════════════════════════════════════════════════════════════
def print_report(s: dict):
    print(f"\n{SEP}")
    print(f"  JAILBREAKBENCH — DATASET INSPECTION REPORT")
    print(f"{SEP}")
    print(f"  Version    : {s['version']}")
    print(f"  Source     : {s['source_url']}")
    print()

    print(f"[1] SAMPLE COUNTS")
    print(f"  Total          : {s['n_total']}")
    print(f"  Harmful        : {s['n_harmful']}")
    print(f"  Benign         : {s['n_benign']}")
    print()

    print(f"[2] COLUMNS & DTYPES (original files)")
    for c, t in s["dtypes"].items():
        print(f"  {c:<25} {t}")
    print()

    print(f"[3] LABEL DISTRIBUTION")
    for lbl, n in s["label_distribution"].items():
        pct = 100 * n / s["n_total"]
        print(f"  {lbl:<20} {n:>4}  ({pct:.1f}%)")
    print()

    print(f"[4] HARMFUL BEHAVIOR CATEGORIES")
    for cat, n in s["harmful_categories"].items():
        print(f"  {cat:<35} {n:>4}")
    print()

    print(f"[5] BENIGN CATEGORIES")
    for cat, n in s["benign_categories"].items():
        print(f"  {cat:<35} {n:>4}")
    print()

    print(f"[6] SOURCE DISTRIBUTION (harmful)")
    for src, n in s["source_distribution"].items():
        print(f"  {src:<25} {n:>4}")
    print()

    print(f"[7] MISSING VALUES  (harmful file)")
    for col, n in s["missing_harmful"].items():
        flag = "  <-- MISSING" if n > 0 else ""
        print(f"  {col:<25} {n:>5}{flag}")
    print()

    print(f"[8] DUPLICATE PROMPTS")
    print(f"  Within harmful set   : {s['n_within_harmful_dup']}")
    print(f"  Within benign set    : {s['n_within_benign_dup']}")
    print(f"  Cross-file (Goal)    : {s['n_cross_file_dup']}")
    print(f"  SHA-256 duplicates   : {s['n_sha256_duplicates']}")
    print()

    print(f"[9] PROMPT LENGTH — Goal column (chars)")
    print(f"  ALL     mean={s['prompt_length_all']['mean']}  "
          f"min={s['prompt_length_all']['min']}  "
          f"max={s['prompt_length_all']['max']}  "
          f"std={s['prompt_length_all']['std']}")
    print(f"  Harmful mean={s['prompt_length_harmful']['mean']}  "
          f"max={s['prompt_length_harmful']['max']}")
    print(f"  Benign  mean={s['prompt_length_benign']['mean']}  "
          f"max={s['prompt_length_benign']['max']}")
    print()

    print(f"[10] LANGUAGE & ENCODING")
    print(f"  Declared language    : {s['language']}")
    print(f"  Non-ASCII prompts    : {s['n_non_ascii_prompts']}")
    print()

    if s["judge_comparison"]:
        print(f"[11] JUDGE-COMPARISON.CSV")
        print(f"  Rows               : {s['judge_comparison']['n_rows']}")
        print(f"  Columns            : {s['judge_comparison']['columns']}")
    print(f"{SEP}\n")


# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    s = inspect()
    print_report(s)
