"""
Phase 1 — Dataset Acquisition
==============================
Covers all sub-phases:
  1.1  HarmBench   — verify + record metadata
  1.2  PIBench     — verify + record metadata
  1.3  Tensor Trust — verify + record schema/utility
  1.4  JailbreakBench — download JBB-Behaviors (harmful + benign)
  1.5  Benign dataset — build diverse benign prompts

Outputs:
  data/raw/harmbench/          (already populated, verified here)
  data/raw/pibench/            (already populated, verified here)
  data/raw/tensor_trust/       (already populated, verified here)
  data/raw/jailbreakbench/     (downloaded here)
  data/raw/benign/             (built here)
  reports/phase1_metadata.json (provenance record)
"""

# ---------------------------------------------------------------------------
# Fix Windows console encoding before any print statements
# ---------------------------------------------------------------------------
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ---------------------------------------------------------------------------
# SSL / cert bypass (corporate proxy environments)
# ---------------------------------------------------------------------------
import os, ssl
os.environ["CURL_CA_BUNDLE"] = ""
ssl._create_default_https_context = ssl._create_unverified_context

import requests, urllib3
urllib3.disable_warnings()
_orig_req = requests.Session.request
def _no_verify(self, method, url, **kw):
    kw["verify"] = False
    return _orig_req(self, method, url, **kw)
requests.Session.request = _no_verify
# ---------------------------------------------------------------------------

import hashlib
import json
import pathlib
import textwrap
from datetime import datetime, timezone

import pandas as pd

# ── project root resolution ─────────────────────────────────────────────────
SCRIPT_DIR  = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
RAW         = PROJECT_ROOT / "data" / "raw"
REPORTS     = PROJECT_ROOT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

HF_BASE = "https://huggingface.co/datasets/JailbreakBench/JBB-Behaviors/resolve/main"

# ── helpers ──────────────────────────────────────────────────────────────────
def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def sha256_file_lf(path: pathlib.Path) -> str:
    """SHA-256 with CRLF normalised to LF (handles Windows git checkout)."""
    content = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(content).hexdigest()

def sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

def banner(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def ok(msg):  print(f"  ✓  {msg}")
def warn(msg): print(f"  ⚠  {msg}")
def info(msg): print(f"  →  {msg}")

# ============================================================================
# 1.1  HarmBench
# ============================================================================
def verify_harmbench(metadata: dict):
    banner("1.1  HarmBench — Verification")

    hb_dir = RAW / "HarmBench"
    expected = {
        "harmbench_behaviors_text_all.csv":  None,
        "harmbench_behaviors_text_test.csv": None,
        "harmbench_behaviors_text_val.csv":  None,
    }

    for fname in expected:
        fpath = hb_dir / fname
        if fpath.exists():
            ok(f"{fname} ({fpath.stat().st_size:,} bytes)")
            expected[fname] = str(fpath)
        else:
            warn(f"MISSING: {fname}")

    # Load master file
    master = hb_dir / "harmbench_behaviors_text_all.csv"
    df = pd.read_csv(master)
    n_all   = len(df)
    cols    = list(df.columns)
    cats    = df["FunctionalCategory"].value_counts().to_dict() if "FunctionalCategory" in df.columns else {}
    sem_cats = df["SemanticCategory"].value_counts().to_dict()  if "SemanticCategory"  in df.columns else {}

    ok(f"Total samples (all):  {n_all}")
    ok(f"Columns: {cols}")
    ok(f"Functional categories: {list(cats.keys())}")
    ok(f"Semantic categories ({len(sem_cats)}): {list(sem_cats.keys())[:10]}...")

    df_test = pd.read_csv(hb_dir / "harmbench_behaviors_text_test.csv")
    df_val  = pd.read_csv(hb_dir / "harmbench_behaviors_text_val.csv")
    ok(f"Test split: {len(df_test)} samples | Val split: {len(df_val)} samples")

    null_prompts = df["Behavior"].isnull().sum() if "Behavior" in df.columns else "N/A"
    avg_len = df["Behavior"].str.len().mean() if "Behavior" in df.columns else 0

    metadata["harmbench"] = {
        "version":          "official (harmbench-behaviors-text v1)",
        "source_url":       "https://github.com/centerforaisafety/HarmBench",
        "paper":            "https://arxiv.org/abs/2402.04249",
        "local_dir":        str(hb_dir),
        "files":            list(expected.keys()),
        "n_samples_all":    n_all,
        "n_samples_test":   len(df_test),
        "n_samples_val":    len(df_val),
        "columns":          cols,
        "functional_categories": cats,
        "semantic_categories":   sem_cats,
        "null_prompts":          int(null_prompts) if isinstance(null_prompts, (int, float)) else null_prompts,
        "avg_prompt_length":     round(float(avg_len), 1),
        "sha256_all":            sha256_file(master),
        "label":                 "all samples are harmful behaviors (jailbreak targets)",
        "verified_at":           datetime.now(timezone.utc).isoformat(),
    }
    ok("HarmBench metadata recorded ✓")


# ============================================================================
# 1.2  PIBench
# ============================================================================
def verify_pibench(metadata: dict):
    banner("1.2  PIBench — Verification")

    pb_dir   = RAW / "pibench" / "dataset" / "v1.0.0"
    meta_f   = pb_dir / "metadata.json"
    full_f   = pb_dir / "full.jsonl"
    inj_f    = pb_dir / "injections.jsonl"
    ben_f    = pb_dir / "benign.jsonl"

    with open(meta_f) as fh:
        pb_meta = json.load(fh)

    ok(f"Version:            {pb_meta['version']}")
    ok(f"Total samples:      {pb_meta['total_samples']}")
    ok(f"Injection samples:  {pb_meta['injection_samples']}")
    ok(f"Benign samples:     {pb_meta['benign_samples']}")

    # Load and verify
    inj_df  = pd.read_json(inj_f, lines=True)
    ben_df  = pd.read_json(ben_f, lines=True)
    full_df = pd.read_json(full_f, lines=True)

    ok(f"Verified injections.jsonl  → {len(inj_df)} rows, cols={list(inj_df.columns)}")
    ok(f"Verified benign.jsonl      → {len(ben_df)} rows")
    ok(f"Verified full.jsonl        → {len(full_df)} rows")

    label_col  = "label"   # values: 'injection' | 'benign'
    cat_col    = "category"
    cats = full_df[cat_col].value_counts().to_dict() if cat_col in full_df.columns else {}
    sev  = full_df["severity"].value_counts().to_dict() if "severity" in full_df.columns else {}

    # SHA-256 cross-check (normalise CRLF->LF for Windows compatibility)
    actual_sha   = sha256_file_lf(full_f)
    expected_sha = pb_meta.get("sha256_full_jsonl", "")
    if actual_sha == expected_sha:
        ok(f"SHA-256 match (LF-normalised): {actual_sha[:16]}...")
    else:
        warn(f"SHA-256 mismatch even after LF-normalisation — file may be corrupted")
        warn(f"  expected={expected_sha[:16]}... got={actual_sha[:16]}...")

    metadata["pibench"] = {
        "version":          pb_meta["version"],
        "source_url":       "https://github.com/PIBench/PIBench",
        "local_dir":        str(RAW / "pibench"),
        "n_total":          pb_meta["total_samples"],
        "n_injections":     pb_meta["injection_samples"],
        "n_benign":         pb_meta["benign_samples"],
        "columns":          list(full_df.columns),
        "label_column":     label_col,
        "label_values":     list(full_df[label_col].unique()) if label_col in full_df.columns else [],
        "categories":       cats,
        "severity_counts":  sev,
        "sha256_full":      actual_sha,
        "sha256_match":     actual_sha == expected_sha,
        "verified_at":      datetime.now(timezone.utc).isoformat(),
    }
    ok("PIBench metadata recorded ✓")


# ============================================================================
# 1.3  Tensor Trust
# ============================================================================
def verify_tensor_trust(metadata: dict):
    banner("1.3  Tensor Trust — Verification & Schema Inspection")

    tt_dir   = RAW / "tensor_trust"
    hij_f    = tt_dir / "benchmarks" / "hijacking-robustness" / "v1" / "hijacking_robustness_dataset.jsonl"
    ext_f    = tt_dir / "benchmarks" / "extraction-robustness" / "v1" / "extraction_robustness_dataset.jsonl"

    # Hijacking benchmark
    hij_df = pd.read_json(hij_f, lines=True)
    ok(f"Hijacking benchmark: {len(hij_df)} samples, cols={list(hij_df.columns)}")

    # Extraction benchmark
    ext_df = pd.read_json(ext_f, lines=True)
    ok(f"Extraction benchmark: {len(ext_df)} samples, cols={list(ext_df.columns)}")

    # Schema interpretation
    # hijacking: sample_id, pre_prompt, access_code, post_prompt, attack
    # → attack field = the adversarial injection attempt
    # → pre_prompt+post_prompt = the LLM system prompt (defense)
    # These are prompt injection attacks against a defended LLM
    info("Hijacking schema: 'attack' column = prompt injection payload")
    info("Extraction schema: should have 'attack' or similar injection column")

    # Determine useful columns
    hij_sample_count = len(hij_df)
    ext_sample_count = len(ext_df)

    # Both are suitable: attack column = the malicious input (Prompt Injection)
    # We will use:
    #   Training: random 70% of hij + 70% ext
    #   Eval:     remaining 30% (reserved for test/unseen eval)

    metadata["tensor_trust"] = {
        "version":          "benchmarks v1 / raw data v2",
        "source_url":       "https://tensortrust.ai/paper",
        "github":           "https://github.com/HumanCompatibleAI/tensor-trust-data",
        "paper":            "https://arxiv.org/abs/2311.09384",
        "local_dir":        str(tt_dir),
        "benchmarks": {
            "hijacking_robustness": {
                "file":    str(hij_f),
                "n_samples": hij_sample_count,
                "columns":   list(hij_df.columns),
                "label":     "prompt_injection  (attack column is the adversarial input)",
                "sha256":    sha256_file(hij_f),
            },
            "extraction_robustness": {
                "file":    str(ext_f),
                "n_samples": ext_sample_count,
                "columns":   list(ext_df.columns),
                "label":     "prompt_leakage  (attack attempts to extract system prompt)",
                "sha256":    sha256_file(ext_f),
            },
        },
        "recommended_split": {
            "training":   "70%  of each benchmark",
            "evaluation": "30%  reserved for known-attack test set",
        },
        "verified_at": datetime.now(timezone.utc).isoformat(),
    }
    ok("Tensor Trust metadata recorded ✓")


# ============================================================================
# 1.4  JailbreakBench
# ============================================================================
def download_jailbreakbench(metadata: dict):
    banner("1.4  JailbreakBench — Download JBB-Behaviors")

    jbb_dir = RAW / "jailbreakbench"
    jbb_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "harmful-behaviors.csv":  f"{HF_BASE}/data/harmful-behaviors.csv",
        "benign-behaviors.csv":   f"{HF_BASE}/data/benign-behaviors.csv",
        "judge-comparison.csv":   f"{HF_BASE}/data/judge-comparison.csv",
    }

    downloaded = {}
    for fname, url in files.items():
        out_path = jbb_dir / fname
        if out_path.exists() and out_path.stat().st_size > 100:
            ok(f"Already downloaded: {fname}")
            downloaded[fname] = str(out_path)
            continue
        info(f"Downloading {fname} …")
        try:
            resp = requests.get(url, timeout=60)
            resp.raise_for_status()
            out_path.write_bytes(resp.content)
            ok(f"Saved {fname} ({out_path.stat().st_size:,} bytes)")
            downloaded[fname] = str(out_path)
        except Exception as e:
            warn(f"Failed to download {fname}: {e}")
            downloaded[fname] = None

    # Load and inspect
    harm_f = jbb_dir / "harmful-behaviors.csv"
    ben_f  = jbb_dir / "benign-behaviors.csv"

    jbb_meta = {
        "version":   "JBB-Behaviors v1.0 (HuggingFace)",
        "source_url": "https://huggingface.co/datasets/JailbreakBench/JBB-Behaviors",
        "paper":      "https://arxiv.org/abs/2404.01318",
        "local_dir":  str(jbb_dir),
        "files":      downloaded,
        "verified_at": datetime.now(timezone.utc).isoformat(),
    }

    if harm_f.exists():
        harm_df = pd.read_csv(harm_f)
        ok(f"harmful-behaviors.csv: {len(harm_df)} rows, cols={list(harm_df.columns)}")
        jbb_meta["n_harmful"]        = len(harm_df)
        jbb_meta["harmful_columns"]  = list(harm_df.columns)
        jbb_meta["sha256_harmful"]   = sha256_file(harm_f)
        if "Category" in harm_df.columns:
            jbb_meta["harm_categories"] = harm_df["Category"].value_counts().to_dict()

    if ben_f.exists():
        ben_df = pd.read_csv(ben_f)
        ok(f"benign-behaviors.csv: {len(ben_df)} rows, cols={list(ben_df.columns)}")
        jbb_meta["n_benign"]        = len(ben_df)
        jbb_meta["benign_columns"]  = list(ben_df.columns)
        jbb_meta["sha256_benign"]   = sha256_file(ben_f)

    metadata["jailbreakbench"] = jbb_meta
    ok("JailbreakBench metadata recorded ✓")


# ============================================================================
# 1.5  Benign Dataset
# ============================================================================
BENIGN_PROMPTS = {
    # --- General user queries ---
    "general": [
        "What's a good recipe for vegetarian chili?",
        "Can you explain how photosynthesis works?",
        "What are the main differences between supervised and unsupervised learning?",
        "How do I make sourdough bread at home?",
        "What is the capital of Brazil and what is it known for?",
        "How long does it take to fly from New York to Tokyo?",
        "What are some tips for improving sleep quality?",
        "Can you recommend some classic novels to read this summer?",
        "What is the difference between a meteor and a meteorite?",
        "How does the stock market work?",
        "What are the symptoms of vitamin D deficiency?",
        "How can I reduce my carbon footprint?",
        "What are the best practices for staying hydrated during exercise?",
        "Can you explain the concept of compound interest?",
        "What is the history of the Olympics?",
        "How do vaccines work at a biological level?",
        "What are some effective strategies for time management?",
        "How do I get started with meditation?",
        "What causes the northern lights (aurora borealis)?",
        "What is the difference between a democracy and a republic?",
    ],
    # --- Coding queries ---
    "coding": [
        "Can you help me write a Python function that reverses a linked list?",
        "How do I center a div in CSS?",
        "What is the difference between == and === in JavaScript?",
        "How do I implement binary search in Python?",
        "Can you explain what a REST API is?",
        "What is the difference between a list and a tuple in Python?",
        "How do I handle exceptions in Java?",
        "What is a closure in JavaScript and when would you use one?",
        "How do I create a virtual environment in Python?",
        "Can you explain what Docker containers are?",
        "What is recursion and can you give a simple example?",
        "How do I write a SQL query to find duplicate records?",
        "What is the difference between GET and POST HTTP methods?",
        "How do I sort a list of dictionaries by a specific key in Python?",
        "What is a hash table and how does it work?",
        "Can you help me debug this Python code: `print('Hello World'`?",
        "What is the difference between synchronous and asynchronous programming?",
        "How do I use list comprehensions in Python?",
        "What is a foreign key in a relational database?",
        "How do I implement pagination in a web application?",
    ],
    # --- Educational queries ---
    "educational": [
        "Can you explain the theory of relativity in simple terms?",
        "What were the main causes of World War I?",
        "How does the human immune system work?",
        "What is the Pythagorean theorem and how is it used?",
        "Can you explain the concept of entropy in thermodynamics?",
        "What is the difference between mitosis and meiosis?",
        "How did the Renaissance period influence modern art?",
        "What is quantum entanglement?",
        "Can you explain how supply and demand affect prices?",
        "What is the significance of the Magna Carta?",
        "How do black holes form?",
        "What is the water cycle and why is it important?",
        "Can you explain Maslow's hierarchy of needs?",
        "What were the key contributions of Isaac Newton to science?",
        "How does evolution work according to Darwin's theory?",
        "What is the difference between weather and climate?",
        "Can you explain the concept of opportunity cost in economics?",
        "What is the structure of DNA?",
        "How did the Industrial Revolution change society?",
        "What is cognitive bias and can you give examples?",
    ],
    # --- Technical queries ---
    "technical": [
        "What is the difference between TCP and UDP protocols?",
        "How does HTTPS encryption work?",
        "What is a load balancer and why is it used?",
        "Can you explain what microservices architecture means?",
        "What is the difference between RAM and ROM?",
        "How does a CPU cache work?",
        "What is continuous integration and continuous deployment (CI/CD)?",
        "Can you explain what Kubernetes is and what it does?",
        "What is the difference between SQL and NoSQL databases?",
        "How does DNS resolution work?",
        "What is a CDN (Content Delivery Network) and how does it help performance?",
        "Can you explain the OSI model of network communication?",
        "What is Agile methodology in software development?",
        "How does garbage collection work in programming languages?",
        "What is the difference between a compiler and an interpreter?",
        "Can you explain what an API gateway does?",
        "What is eventual consistency in distributed systems?",
        "How does version control with Git work?",
        "What is a webhook and how is it different from polling?",
        "Can you explain the concept of idempotency in APIs?",
    ],
    # --- Security-related legitimate queries ---
    "security_legitimate": [
        "What are the best practices for creating a strong password?",
        "How does two-factor authentication improve account security?",
        "What is phishing and how can I recognize a phishing email?",
        "Can you explain what a VPN is and when I should use one?",
        "What is the difference between symmetric and asymmetric encryption?",
        "How do I safely store passwords in a web application?",
        "What is a SQL injection attack and how can developers prevent it?",
        "What does GDPR require companies to do with personal data?",
        "How do I check if a website is secure before entering my credit card?",
        "What is a firewall and how does it protect a network?",
        "What are the most common types of malware and how do they spread?",
        "How do I enable full-disk encryption on my laptop?",
        "What is the principle of least privilege in cybersecurity?",
        "Can you explain what a zero-day vulnerability is?",
        "What are some signs that my computer might be infected with malware?",
        "How do I securely delete files from my hard drive?",
        "What is a man-in-the-middle attack and how can it be prevented?",
        "What is the purpose of a security audit?",
        "How does HTTPS protect data in transit?",
        "What are common security risks in public Wi-Fi networks?",
    ],
    # --- RAG-related legitimate queries ---
    "rag_legitimate": [
        "Can you summarize the key points from this document?",
        "Based on the provided context, what does the author argue about climate change?",
        "According to the text, what are the three main factors affecting productivity?",
        "Can you find all mentions of the term 'machine learning' in the document?",
        "What does the research paper say about the methodology used?",
        "Based on the retrieved articles, what are the common themes?",
        "Can you help me find the definition of 'transformer architecture' in my notes?",
        "What year was the regulation mentioned in the document introduced?",
        "Based on the context provided, what is the recommended dosage?",
        "Can you extract all the action items from this meeting transcript?",
        "What does the contract say about termination clauses?",
        "Based on the provided FAQ, how do I reset my account password?",
        "Can you find all references to 'data privacy' in the policy document?",
        "What is the conclusion of the research paper provided?",
        "According to the provided text, what are the main risks identified?",
        "Based on the retrieved documents, what are the differences between Plan A and Plan B?",
        "Can you summarize the financial results from the provided quarterly report?",
        "What does the technical documentation say about API rate limits?",
        "Based on the context, what steps should I follow for onboarding?",
        "Can you extract all the named entities from the provided text?",
    ],
}


def build_benign_dataset(metadata: dict):
    banner("1.5  Benign Dataset — Building Diverse Collection")

    ben_dir = RAW / "benign"
    ben_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for category, prompts in BENIGN_PROMPTS.items():
        for i, prompt in enumerate(prompts, 1):
            rows.append({
                "id":          f"benign_{category}_{i:03d}",
                "text":        prompt,
                "label":       "benign",
                "category":    category,
                "source":      "curated_synthetic",
                "language":    "en",
                "notes":       f"Diverse benign prompt — {category.replace('_', ' ')} category",
            })

    df = pd.DataFrame(rows)
    out_path = ben_dir / "benign_diverse.jsonl"
    df.to_json(out_path, orient="records", lines=True, force_ascii=False)

    # Also export as CSV
    csv_path = ben_dir / "benign_diverse.csv"
    df.to_csv(csv_path, index=False)

    category_counts = df["category"].value_counts().to_dict()
    ok(f"Total benign prompts: {len(df)}")
    for cat, n in category_counts.items():
        ok(f"  {cat:<30} {n} prompts")

    metadata["benign"] = {
        "version":          "1.0 (curated diverse)",
        "source":           "curated_synthetic — hand-crafted by category",
        "local_dir":        str(ben_dir),
        "files":            ["benign_diverse.jsonl", "benign_diverse.csv"],
        "n_total":          len(df),
        "category_counts":  category_counts,
        "categories": [
            "general",
            "coding",
            "educational",
            "technical",
            "security_legitimate",
            "rag_legitimate",
        ],
        "label":            "benign (all prompts)",
        "diversity_note":   "Covers general, coding, educational, technical, legitimate security, and RAG queries. Designed so that no prompt looks suspicious to a human reviewer.",
        "sha256_jsonl":     sha256_file(out_path),
        "created_at":       datetime.now(timezone.utc).isoformat(),
    }
    ok("Benign dataset saved ✓")


# ============================================================================
# Custom JSON encoder — handles numpy int64/float64 from pandas value_counts
# ============================================================================
import numpy as np

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


# ============================================================================
# Save metadata report
# ============================================================================
def save_metadata(metadata: dict):
    banner("Saving Phase 1 Metadata Report")

    metadata["phase1_summary"] = {
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "datasets": {
            "harmbench":       metadata.get("harmbench", {}).get("n_samples_all", 0),
            "pibench":         metadata.get("pibench", {}).get("n_total", 0),
            "tensor_trust_hijacking": (
                metadata.get("tensor_trust", {})
                        .get("benchmarks", {})
                        .get("hijacking_robustness", {})
                        .get("n_samples", 0)
            ),
            "tensor_trust_extraction": (
                metadata.get("tensor_trust", {})
                        .get("benchmarks", {})
                        .get("extraction_robustness", {})
                        .get("n_samples", 0)
            ),
            "jailbreakbench_harmful": metadata.get("jailbreakbench", {}).get("n_harmful", 0),
            "jailbreakbench_benign":  metadata.get("jailbreakbench", {}).get("n_benign", 0),
            "benign_diverse":         metadata.get("benign", {}).get("n_total", 0),
        },
    }

    totals = metadata["phase1_summary"]["datasets"]
    grand_total = sum(totals.values())
    metadata["phase1_summary"]["grand_total_raw_samples"] = grand_total

    out_path = REPORTS / "phase1_metadata.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2, ensure_ascii=False, cls=NumpyEncoder)

    ok(f"Metadata saved -> {out_path}")
    print()
    print("  +--- PHASE 1 SUMMARY -------------------------------------------+")
    for ds, n in totals.items():
        print(f"  |  {ds:<40} {int(n):>6} samples |")
    print(f"  |  {'GRAND TOTAL':<40} {int(grand_total):>6} samples |")
    print("  +---------------------------------------------------------------+")


# ============================================================================
# Main
# ============================================================================
def main():
    print(f"\n{'#'*60}")
    print(f"  PHASE 1 — DATASET ACQUISITION")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")

    metadata = {}

    verify_harmbench(metadata)
    verify_pibench(metadata)
    verify_tensor_trust(metadata)
    download_jailbreakbench(metadata)
    build_benign_dataset(metadata)
    save_metadata(metadata)

    print(f"\n{'#'*60}")
    print(f"  PHASE 1 COMPLETE ✓")
    print(f"{'#'*60}\n")


if __name__ == "__main__":
    main()
