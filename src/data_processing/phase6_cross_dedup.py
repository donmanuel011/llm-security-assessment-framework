"""
Phase 6 — Cross-Dataset Deduplication
=======================================
Reads deduped datasets from data/interim/ (dedup_*.csv), performs
cross-dataset exact and near-duplicate detection across all dataset pairs,
removes overlapping prompts (keeping them in the higher-priority dataset),
and outputs cross-deduped files: xdedup_*.csv.

Logs cross-dataset overlap statistics to reports/cross_dedup_report.csv.

Priority order (highest priority = kept when found in multiple datasets):
  1. HarmBench  2. JailbreakBench  3. PIBench  4. Tensor Trust  5. Benign
"""

import sys
import io
import os
import ssl

# Force UTF-8 output on Windows to prevent cp1252 UnicodeEncodeErrors
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import pathlib
import pandas as pd
import hashlib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import warnings
import itertools
import torch

warnings.filterwarnings("ignore")

# ── SSL fix ───────────────────────────────────────────────────────────────────
os.environ["HF_HUB_DISABLE_SSL_VERIFICATION"] = "1"
os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""
_orig_ctx = ssl.create_default_context
def _no_verify_ctx(*a, **kw):
    ctx = _orig_ctx(*a, **kw)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx
ssl.create_default_context = _no_verify_ctx

# ── paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
INTERIM_DIR  = PROJECT_ROOT / "data" / "interim"
REPORTS_DIR  = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Priority order — when a prompt appears in multiple datasets,
# it is KEPT in the dataset with the LOWEST priority_rank and
# REMOVED from all higher-rank datasets.
DATASET_FILES = [
    ("HarmBench",    "dedup_harmbench.csv"),
    ("JailbreakBench", "dedup_jailbreakbench.csv"),
    ("PIBench",      "dedup_pibench.csv"),
    ("TensorTrust",  "dedup_tensor_trust.csv"),
    ("Benign",       "dedup_benign.csv"),
]

TFIDF_THRESHOLD   = 0.95
SEMANTIC_THRESHOLD = 0.95

def banner(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def get_sha256(text: str) -> str:
    if pd.isna(text):
        return ""
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()


def cross_dedup_pair(df_a: pd.DataFrame, df_b: pd.DataFrame,
                     name_a: str, name_b: str,
                     st_model,
                     tfidf_sim_threshold: float = TFIDF_THRESHOLD,
                     semantic_sim_threshold: float = SEMANTIC_THRESHOLD
                     ) -> tuple[set, set, dict]:
    """
    Compares df_a and df_b. Returns:
      - set of indices in df_b to drop (duplicates found in df_a)
      - stats dict
    Priority: df_a wins (higher priority), drop matches from df_b.
    """
    stats = {"pair": f"{name_a} <-> {name_b}", "exact": 0, "lexical": 0, "semantic": 0}
    hashes_a = set(df_a["prompt_hash"])
    
    b_to_drop = set()

    # 1. Exact (hash-based)
    for idx, row in df_b.iterrows():
        if row["prompt_hash"] in hashes_a:
            b_to_drop.add(idx)
    stats["exact"] = len(b_to_drop)
    print(f"    Exact overlaps: {stats['exact']}")

    # Work only on remaining rows in df_b for near-dup checks
    remaining_b = df_b.drop(index=list(b_to_drop))
    if remaining_b.empty or df_a.empty:
        return b_to_drop, stats

    prompts_a = df_a["prompt"].tolist()
    prompts_b = remaining_b["prompt"].tolist()
    all_prompts = prompts_a + prompts_b

    # 2. Lexical (TF-IDF)
    try:
        vectorizer = TfidfVectorizer(lowercase=True, stop_words="english", min_df=1)
        tfidf_matrix = vectorizer.fit_transform(all_prompts)
        len_a = len(prompts_a)
        sim_matrix = cosine_similarity(tfidf_matrix[:len_a], tfidf_matrix[len_a:])

        lexical_drop_local = set()
        for i in range(len_a):
            for j in range(len(prompts_b)):
                if sim_matrix[i, j] >= tfidf_sim_threshold:
                    lexical_drop_local.add(j)

        real_b_indices = list(remaining_b.index)
        new_lexical = {real_b_indices[j] for j in lexical_drop_local}
        b_to_drop.update(new_lexical)
        stats["lexical"] = len(new_lexical)
        print(f"    Lexical near-duplicates: {stats['lexical']}")
    except ValueError:
        print("    [WARN] TF-IDF failed. Skipping lexical cross-dedup.")

    # 3. Semantic (Sentence-Transformers)
    remaining_b2 = df_b.drop(index=list(b_to_drop))
    if remaining_b2.empty:
        return b_to_drop, stats

    prompts_a2 = df_a["prompt"].tolist()
    prompts_b2 = remaining_b2["prompt"].tolist()

    emb_a = st_model.encode(prompts_a2, convert_to_tensor=True, show_progress_bar=False)
    emb_b = st_model.encode(prompts_b2, convert_to_tensor=True, show_progress_bar=False)
    sim_sem = torch.nn.functional.cosine_similarity(
        emb_a.unsqueeze(1), emb_b.unsqueeze(0), dim=2
    ).cpu().numpy()

    semantic_drop_local = set()
    for i in range(len(prompts_a2)):
        for j in range(len(prompts_b2)):
            if sim_sem[i, j] >= semantic_sim_threshold:
                semantic_drop_local.add(j)

    real_b2_indices = list(remaining_b2.index)
    new_semantic = {real_b2_indices[j] for j in semantic_drop_local}
    b_to_drop.update(new_semantic)
    stats["semantic"] = len(new_semantic)
    print(f"    Semantic near-duplicates: {stats['semantic']}")

    return b_to_drop, stats


def main():
    print(f"\n{'#'*60}")
    print(f"  PHASE 6 — CROSS-DATASET DEDUPLICATION")
    print(f"{'#'*60}")

    from sentence_transformers import SentenceTransformer
    print("  Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
    st_model = SentenceTransformer("all-MiniLM-L6-v2")
    print("  Model loaded.\n")

    # Load all datasets
    datasets = {}
    for name, fname in DATASET_FILES:
        path = INTERIM_DIR / fname
        if not path.exists():
            print(f"  [WARN] Missing: {fname} — skipping.")
            continue
        df = pd.read_csv(path)
        df["prompt"] = df["prompt"].fillna("")
        df["prompt_hash"] = df["prompt"].apply(get_sha256)
        datasets[name] = df
        print(f"  Loaded {len(df):>5} rows from {fname}")

    # indices to drop per dataset
    drop_indices: dict[str, set] = {name: set() for name in datasets}
    pair_reports = []

    # Process all ordered pairs (A has higher priority than B)
    dataset_names = [name for name, _ in DATASET_FILES if name in datasets]
    for name_a, name_b in itertools.combinations(dataset_names, 2):
        banner(f"{name_a} <-> {name_b}")
        df_a = datasets[name_a].drop(index=list(drop_indices[name_a]))
        df_b = datasets[name_b].drop(index=list(drop_indices[name_b]))
        b_to_drop, stats = cross_dedup_pair(df_a, df_b, name_a, name_b, st_model)
        drop_indices[name_b].update(b_to_drop)
        total = stats["exact"] + stats["lexical"] + stats["semantic"]
        print(f"  >> Total removed from {name_b}: {total}")
        pair_reports.append({
            "pair": f"{name_a} <-> {name_b}",
            "exact_overlaps": stats["exact"],
            "lexical_overlaps": stats["lexical"],
            "semantic_overlaps": stats["semantic"],
            "total_removed_from_lower_priority": total,
        })

    print(f"\n{'='*60}")
    print("  Saving cross-deduplicated datasets...")
    print(f"{'='*60}")

    name_to_file = {name: fname for name, fname in DATASET_FILES}
    for name in dataset_names:
        df = datasets[name].drop(index=list(drop_indices[name])).reset_index(drop=True)
        df.drop(columns=["prompt_hash"], inplace=True, errors="ignore")
        out_fname = name_to_file[name].replace("dedup_", "xdedup_")
        out_path = INTERIM_DIR / out_fname
        df.to_csv(out_path, index=False)
        removed = len(drop_indices[name])
        print(f"  [+] {name}: {len(datasets[name])} → {len(df)} rows ({removed} cross-dups removed) → {out_fname}")

    # Save pair-level report
    report_df = pd.DataFrame(pair_reports)
    report_path = REPORTS_DIR / "cross_dedup_report.csv"
    report_df.to_csv(report_path, index=False)
    print(f"\n  [+] Cross-dedup report saved -> {report_path}")

    print(f"\n{'#'*60}")
    print(f"  PHASE 6 COMPLETE [OK]")
    print(f"{'#'*60}\n")


if __name__ == "__main__":
    main()
