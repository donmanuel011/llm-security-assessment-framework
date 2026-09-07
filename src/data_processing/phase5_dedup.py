"""
Phase 5 — Deduplication (Within-Dataset)
========================================
Reads cleaned datasets from data/interim/, performs exact, lexical, 
and semantic deduplication, and outputs dedup_*.csv.
Logs the results to reports/deduplication_report.csv.
"""

import os
import pathlib
import pandas as pd
import hashlib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import warnings
import torch
import ssl

# Suppress some noisy warnings from huggingface/transformers
warnings.filterwarnings("ignore")

# ── SSL fix (self-signed / corporate certs) ───────────────────────────────────
os.environ["HF_HUB_DISABLE_SSL_VERIFICATION"] = "1"
os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""

# Patch the default SSL context to not verify certificates
_orig_create_default_context = ssl.create_default_context
def _ssl_ctx_no_verify(*args, **kwargs):
    ctx = _orig_create_default_context(*args, **kwargs)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx
ssl.create_default_context = _ssl_ctx_no_verify


# ── paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
INTERIM_DIR  = PROJECT_ROOT / "data" / "interim"
REPORTS_DIR  = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def banner(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def get_sha256(text: str) -> str:
    if pd.isna(text):
        return ""
    return hashlib.sha256(str(text).encode('utf-8')).hexdigest()

def process_dataset(filename: str, st_model, report_data: list):
    input_path = INTERIM_DIR / filename
    if not input_path.exists():
        print(f"  [WARN] File not found: {input_path.name}")
        return
    
    df = pd.read_csv(input_path)
    initial_len = len(df)
    print(f"  Loaded {initial_len} rows from {filename}")
    
    if initial_len == 0:
        return
        
    df['prompt'] = df['prompt'].fillna('')
    
    # 1. Exact Duplicate Detection via SHA-256
    df['prompt_hash'] = df['prompt'].apply(get_sha256)
    before_exact = len(df)
    df = df.drop_duplicates(subset=['prompt_hash'], keep='first').copy()
    exact_dups = before_exact - len(df)
    print(f"  [-] Removed {exact_dups} exact duplicates (SHA-256).")
    
    df = df.reset_index(drop=True)
    if len(df) < 2:
        out_filename = filename.replace("clean_", "dedup_")
        df.to_csv(INTERIM_DIR / out_filename, index=False)
        report_data.append({
            "dataset": filename, "initial_rows": initial_len, 
            "exact_removed": exact_dups, "lexical_removed": 0, 
            "semantic_removed": 0, "final_rows": len(df)
        })
        return

    # 2. Lexical Near-Duplicate Detection (TF-IDF + Cosine Similarity)
    prompts = df['prompt'].tolist()
    vectorizer = TfidfVectorizer(lowercase=True, stop_words='english', min_df=1)
    try:
        tfidf_matrix = vectorizer.fit_transform(prompts)
        cos_sim_tfidf = cosine_similarity(tfidf_matrix)
        
        # Upper triangle without diagonal
        np.fill_diagonal(cos_sim_tfidf, 0)
        
        to_drop_lexical = set()
        # Iterate over the similarity matrix to find pairs > 0.95
        # We keep the first one (lower index) and drop the latter
        for i in range(len(prompts)):
            if i in to_drop_lexical: continue
            for j in range(i + 1, len(prompts)):
                if cos_sim_tfidf[i, j] > 0.95:
                    to_drop_lexical.add(j)
                    
        df = df.drop(index=list(to_drop_lexical)).reset_index(drop=True)
        lexical_dups = len(to_drop_lexical)
        print(f"  [-] Removed {lexical_dups} lexical near-duplicates (TF-IDF > 0.95).")
    except ValueError:
        print("  [WARN] TF-IDF failed (possibly empty vocabulary). Skipping lexical dedup.")
        lexical_dups = 0

    if len(df) < 2:
        out_filename = filename.replace("clean_", "dedup_")
        df.to_csv(INTERIM_DIR / out_filename, index=False)
        report_data.append({
            "dataset": filename, "initial_rows": initial_len, 
            "exact_removed": exact_dups, "lexical_removed": lexical_dups, 
            "semantic_removed": 0, "final_rows": len(df)
        })
        return

    # 3. Semantic Near-Duplicate Detection (Sentence-Transformers)
    prompts = df['prompt'].tolist()
    embeddings = st_model.encode(prompts, convert_to_tensor=True, show_progress_bar=False)
    
    # Cosine similarity in PyTorch
    cos_sim_sem = torch.nn.functional.cosine_similarity(embeddings.unsqueeze(1), embeddings.unsqueeze(0), dim=2)
    cos_sim_sem = cos_sim_sem.cpu().numpy()
    np.fill_diagonal(cos_sim_sem, 0)
    
    to_drop_semantic = set()
    for i in range(len(prompts)):
        if i in to_drop_semantic: continue
        for j in range(i + 1, len(prompts)):
            if cos_sim_sem[i, j] > 0.95:
                to_drop_semantic.add(j)
                
    df = df.drop(index=list(to_drop_semantic)).reset_index(drop=True)
    semantic_dups = len(to_drop_semantic)
    print(f"  [-] Removed {semantic_dups} semantic near-duplicates (Embeddings > 0.95).")
    
    # Save Output
    out_filename = filename.replace("clean_", "dedup_")
    out_path = INTERIM_DIR / out_filename
    df.drop(columns=['prompt_hash'], inplace=True, errors='ignore')
    df.to_csv(out_path, index=False)
    print(f"  [+] Saved {len(df)} deduped rows -> {out_filename}")
    
    report_data.append({
        "dataset": filename,
        "initial_rows": initial_len,
        "exact_removed": exact_dups,
        "lexical_removed": lexical_dups,
        "semantic_removed": semantic_dups,
        "final_rows": len(df)
    })

def main():
    print(f"\n{'#'*60}")
    print(f"  PHASE 5 — DATA DEDUPLICATION")
    print(f"{'#'*60}")
    
    # Import here to avoid overhead if script fails early
    from sentence_transformers import SentenceTransformer
    print("  Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
    st_model = SentenceTransformer('all-MiniLM-L6-v2')
    print("  Model loaded.")
    
    datasets = [
        "clean_harmbench.csv",
        "clean_pibench.csv",
        "clean_tensor_trust.csv",
        "clean_jailbreakbench.csv",
        "clean_benign.csv"
    ]
    
    report_data = []
    
    for ds in datasets:
        banner(f"Processing {ds}")
        process_dataset(ds, st_model, report_data)

    # Save report
    report_df = pd.DataFrame(report_data)
    report_path = REPORTS_DIR / "deduplication_report.csv"
    report_df.to_csv(report_path, index=False)
    print(f"\n  [+] Saved deduplication report -> {report_path}")

    print(f"\n{'#'*60}")
    print(f"  PHASE 5 COMPLETE [OK]")
    print(f"{'#'*60}\n")

if __name__ == "__main__":
    main()
