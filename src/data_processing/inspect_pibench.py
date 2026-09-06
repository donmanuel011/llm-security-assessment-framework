"""
inspect_pibench.py
==================
Standalone inspection script for the PIBench dataset.

Outputs a structured summary dict (returned by inspect()) and prints a
human-readable report to stdout.

Dataset location: data/raw/pibench/dataset/v1.0.0/
Files:
  full.jsonl       – 82 rows (all samples)
  injections.jsonl – 66 injection samples
  benign.jsonl     – 16 benign samples
  metadata.json    – dataset metadata

Schema (per row):
  id, version, label, category, technique, severity, channel, text, source, notes

Label values: "injection" | "benign"
"""

import sys, io, pathlib, hashlib, json

import pandas as pd

# ── paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
PB_DIR       = PROJECT_ROOT / "data" / "raw" / "pibench" / "dataset" / "v1.0.0"

SEP  = "=" * 60


# ═══════════════════════════════════════════════════════════════════════════════
def inspect(project_root: pathlib.Path | None = None) -> dict:
    root   = pathlib.Path(project_root) if project_root else PROJECT_ROOT
    pb_dir = root / "data" / "raw" / "pibench" / "dataset" / "v1.0.0"

    full_f = pb_dir / "full.jsonl"
    inj_f  = pb_dir / "injections.jsonl"
    ben_f  = pb_dir / "benign.jsonl"
    meta_f = pb_dir / "metadata.json"

    with open(meta_f, encoding="utf-8") as fh:
        meta = json.load(fh)

    df     = pd.read_json(full_f,  lines=True)
    inj_df = pd.read_json(inj_f,   lines=True)
    ben_df = pd.read_json(ben_f,   lines=True)

    prompt_col = "text"
    label_col  = "label"

    # ── basic ─────────────────────────────────────────────────────────────────
    n_total  = len(df)
    columns  = list(df.columns)
    dtypes   = {c: str(t) for c, t in df.dtypes.items()}

    # ── label distribution ────────────────────────────────────────────────────
    label_dist = df[label_col].value_counts().to_dict() if label_col in df.columns else {}

    # ── attack categories ─────────────────────────────────────────────────────
    cat_dist      = df["category"].value_counts().to_dict()   if "category"  in df.columns else {}
    tech_dist     = df["technique"].value_counts().to_dict()  if "technique" in df.columns else {}
    sev_dist      = df["severity"].value_counts().to_dict()   if "severity"  in df.columns else {}
    channel_dist  = df["channel"].value_counts().to_dict()    if "channel"   in df.columns else {}

    # ── injection-only category breakdown ─────────────────────────────────────
    inj_cat_dist  = inj_df["category"].value_counts().to_dict() if "category" in inj_df.columns else {}

    # ── missing values ────────────────────────────────────────────────────────
    missing = {c: int(df[c].isnull().sum()) for c in df.columns}

    # ── duplicates ────────────────────────────────────────────────────────────
    n_exact_dup = int(df.duplicated(subset=[prompt_col]).sum())
    sha_series  = df[prompt_col].dropna().apply(
        lambda t: hashlib.sha256(str(t).strip().encode()).hexdigest()
    )
    n_sha_dup   = int(sha_series.duplicated().sum())

    # ── prompt length ─────────────────────────────────────────────────────────
    lengths   = df[prompt_col].dropna().str.len()
    len_stats = {
        "min":    int(lengths.min()),
        "max":    int(lengths.max()),
        "mean":   round(float(lengths.mean()), 1),
        "median": round(float(lengths.median()), 1),
        "std":    round(float(lengths.std()), 1),
    }

    # injection vs benign prompt length comparison
    inj_lengths = inj_df[prompt_col].dropna().str.len()
    ben_lengths = ben_df[prompt_col].dropna().str.len()

    # ── non-ASCII ─────────────────────────────────────────────────────────────
    non_ascii = int(
        df[prompt_col].dropna().str.contains(r"[^\x00-\x7F]", regex=True).sum()
    )

    # ── SHA-256 integrity check ────────────────────────────────────────────────
    raw_sha    = hashlib.sha256(full_f.read_bytes()).hexdigest()
    lf_sha     = hashlib.sha256(full_f.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    exp_sha    = meta.get("sha256_full_jsonl", "")
    sha_ok     = (lf_sha == exp_sha)

    summary = {
        "dataset":              "PIBench",
        "version":              meta.get("version", "1.0.0"),
        "source_url":           "https://github.com/PIBench/PIBench",
        "local_dir":            str(pb_dir.parent.parent),
        "prompt_column":        prompt_col,
        "label_column":         label_col,
        "label_values":         list(df[label_col].unique()) if label_col in df.columns else [],
        "language":             "en",
        "n_total":              n_total,
        "n_injections":         len(inj_df),
        "n_benign":             len(ben_df),
        "columns":              columns,
        "dtypes":               dtypes,
        "label_distribution":   {k: int(v) for k, v in label_dist.items()},
        "category_distribution":{k: int(v) for k, v in cat_dist.items()},
        "technique_distribution":{k: int(v) for k, v in tech_dist.items()},
        "severity_distribution":{k: int(v) for k, v in sev_dist.items()},
        "channel_distribution": {k: int(v) for k, v in channel_dist.items()},
        "injection_categories": {k: int(v) for k, v in inj_cat_dist.items()},
        "missing_values":       missing,
        "n_exact_duplicates":   n_exact_dup,
        "n_sha256_duplicates":  n_sha_dup,
        "prompt_length_all":    len_stats,
        "prompt_length_injections": {
            "mean": round(float(inj_lengths.mean()), 1),
            "max":  int(inj_lengths.max()),
        },
        "prompt_length_benign": {
            "mean": round(float(ben_lengths.mean()), 1),
            "max":  int(ben_lengths.max()),
        },
        "n_non_ascii_prompts":  non_ascii,
        "sha256_integrity":     sha_ok,
        "attack_categories":    list(cat_dist.keys()),
        "source_metadata":      ["id", "version", "technique", "severity", "channel", "source", "notes"],
    }
    return summary


# ═══════════════════════════════════════════════════════════════════════════════
def print_report(s: dict):
    print(f"\n{SEP}")
    print(f"  PIBENCH — DATASET INSPECTION REPORT")
    print(f"{SEP}")
    print(f"  Version    : {s['version']}")
    print(f"  Source     : {s['source_url']}")
    print(f"  SHA-256 OK : {s['sha256_integrity']}")
    print()

    print(f"[1] SAMPLE COUNTS")
    print(f"  Total          : {s['n_total']}")
    print(f"  Injections     : {s['n_injections']}")
    print(f"  Benign         : {s['n_benign']}")
    print()

    print(f"[2] COLUMNS & DTYPES")
    for c, t in s["dtypes"].items():
        print(f"  {c:<25} {t}")
    print()

    print(f"[3] LABEL DISTRIBUTION  (column: '{s['label_column']}')")
    for lbl, n in s["label_distribution"].items():
        pct = 100 * n / s["n_total"]
        print(f"  {lbl:<20} {n:>4}  ({pct:.1f}%)")
    print()

    print(f"[4] ATTACK CATEGORIES (injection samples only)")
    for cat, n in s["injection_categories"].items():
        print(f"  {cat:<35} {n:>4}")
    print()

    print(f"[5] SEVERITY DISTRIBUTION")
    for sev, n in s["severity_distribution"].items():
        print(f"  {sev:<15} {n:>4}")
    print()

    print(f"[6] CHANNEL DISTRIBUTION")
    for ch, n in s["channel_distribution"].items():
        print(f"  {ch:<30} {n:>4}")
    print()

    print(f"[7] MISSING VALUES")
    for col, n in s["missing_values"].items():
        flag = "  <-- MISSING" if n > 0 else ""
        print(f"  {col:<25} {n:>5}{flag}")
    print()

    print(f"[8] DUPLICATE PROMPTS")
    print(f"  Exact duplicates     : {s['n_exact_duplicates']}")
    print(f"  SHA-256 duplicates   : {s['n_sha256_duplicates']}")
    print()

    print(f"[9] PROMPT LENGTH (chars)")
    print(f"  ALL       mean={s['prompt_length_all']['mean']}  "
          f"min={s['prompt_length_all']['min']}  "
          f"max={s['prompt_length_all']['max']}  "
          f"std={s['prompt_length_all']['std']}")
    print(f"  Injection mean={s['prompt_length_injections']['mean']}  "
          f"max={s['prompt_length_injections']['max']}")
    print(f"  Benign    mean={s['prompt_length_benign']['mean']}  "
          f"max={s['prompt_length_benign']['max']}")
    print()

    print(f"[10] LANGUAGE & ENCODING")
    print(f"  Declared language    : {s['language']}")
    print(f"  Non-ASCII prompts    : {s['n_non_ascii_prompts']}")
    print(f"{SEP}\n")


# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    s = inspect()
    print_report(s)
