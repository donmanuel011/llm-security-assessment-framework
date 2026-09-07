"""
Phase 17 -- Unseen Attack Evaluation Subsystem.
Evaluates model generalization across:
  - Known attacks test set
  - Transformed/modified attacks (paraphrased, obfuscated, role-based, multi-turn, contextual)
  - Unseen attack types / novel datasets
Calculates the generalization gap: (Known Test F1 - Unseen Test F1).
Outputs report to reports/unseen_eval_report.csv
"""

import sys
import io
import os
import ssl
import pathlib
import pandas as pd
import numpy as np

SCRIPT_DIR   = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Apply HuggingFace SSL fixes
os.environ["HF_HUB_DISABLE_SSL_VERIFICATION"] = "1"
os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""
ssl._create_default_https_context = ssl._create_unverified_context

import httpx
original_init = httpx.Client.__init__
def new_init(self, *args, **kwargs):
    kwargs['verify'] = False
    original_init(self, *args, **kwargs)
httpx.Client.__init__ = new_init

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from src.detection.predict import predict_prompt
from src.detection.model_config import PROCESSED_DIR, REPORTS_DIR
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

def evaluate_subset(df_subset, subset_name, model_key="tfidf_lr"):
    """
    Evaluates predictions on a subset of dataset.
    """
    if len(df_subset) == 0:
        return {
            "subset": subset_name,
            "count": 0,
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0
        }

    prompts = df_subset["prompt"].tolist()
    y_true = (df_subset["label"] == "malicious").astype(int).tolist()

    preds = []
    for p in prompts:
        res = predict_prompt(p, model_key=model_key)
        preds.append(1 if res["is_attack"] else 0)

    acc = accuracy_score(y_true, preds)
    p, r, f1, _ = precision_recall_fscore_support(y_true, preds, average="binary", zero_division=0)

    return {
        "subset": subset_name,
        "count": len(df_subset),
        "accuracy": round(acc, 4),
        "precision": round(p, 4),
        "recall": round(r, 4),
        "f1_score": round(f1, 4)
    }

def run_unseen_evaluation(model_key="tfidf_lr"):
    print(f"\nRunning Unseen Attack Evaluation for [{model_key}]...")
    split_df = pd.read_csv(PROCESSED_DIR / "split_dataset.csv")
    split_df["prompt"] = split_df["prompt"].fillna("")

    trans_df_path = PROCESSED_DIR / "transformed_attacks.csv"
    if trans_df_path.exists():
        trans_df = pd.read_csv(trans_df_path)
        trans_df["prompt"] = trans_df["prompt"].fillna("")
        trans_df["label"] = "malicious"
    else:
        trans_df = pd.DataFrame()

    results = []

    # 1. Known Test Set
    known_df = split_df[split_df["split"] == "test_known"]
    res_known = evaluate_subset(known_df, "Test Known (In-distribution)", model_key=model_key)
    results.append(res_known)

    # 2. Novel/Unseen Test Set
    novel_df = split_df[split_df["split"] == "test_novel"]
    res_novel = evaluate_subset(novel_df, "Test Novel (Unseen Attacks)", model_key=model_key)
    results.append(res_novel)

    # 3. Transformed Attack Variants
    if len(trans_df) > 0 and "transformation" in trans_df.columns:
        for t_type in trans_df["transformation"].unique():
            t_sub = trans_df[trans_df["transformation"] == t_type]
            res_t = evaluate_subset(t_sub, f"Transformation: {t_type}", model_key=model_key)
            results.append(res_t)

    # Calculate Generalization Gap
    known_f1 = res_known["f1_score"]
    novel_f1 = res_novel["f1_score"]
    gap = round(known_f1 - novel_f1, 4)

    results.append({
        "subset": "Generalization Gap (Known F1 - Novel F1)",
        "count": 0,
        "accuracy": 0.0,
        "precision": 0.0,
        "recall": 0.0,
        "f1_score": gap
    })

    res_df = pd.DataFrame(results)
    out_file = REPORTS_DIR / f"unseen_eval_{model_key}.csv"
    res_df.to_csv(out_file, index=False)
    print(f"Saved unseen evaluation report to {out_file}")
    print(res_df.to_string(index=False))
    return res_df

if __name__ == "__main__":
    run_unseen_evaluation("tfidf_lr")
