"""
Evaluates saved fine-tuned DeBERTa checkpoints (checkpoint-525) with base tokenizer
and updates reports/deberta_metrics.csv.
"""

import sys
import io
import os
import ssl
import pathlib
import pandas as pd
import numpy as np
import torch
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

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

from transformers import AutoTokenizer, AutoModelForSequenceClassification

SCRIPT_DIR    = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT  = SCRIPT_DIR.parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR    = PROJECT_ROOT / "models" / "deberta"
REPORTS_DIR   = PROJECT_ROOT / "reports"

MULTICLASS_LABEL_MAP = {
    "Benign": 0,
    "Prompt Injection": 1,
    "Indirect Prompt Injection": 2,
    "Jailbreak": 3,
    "Prompt Leakage": 4,
}

def find_best_checkpoint(base_dir):
    checkpoints = list(base_dir.glob("checkpoint-*"))
    if checkpoints:
        checkpoints.sort(key=lambda x: int(x.name.split("-")[-1]))
        return checkpoints[-1]
    return base_dir

def evaluate_model_dir(base_dir, task_name, test_df, num_labels, avg_type):
    model_dir = find_best_checkpoint(base_dir)
    print(f"Evaluating {task_name} from checkpoint: {model_dir}...")
    tokenizer = AutoTokenizer.from_pretrained("microsoft/deberta-v3-base")
    model = AutoModelForSequenceClassification.from_pretrained(model_dir)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()

    metrics = []
    for split_name in ["test_known", "test_novel"]:
        sub = test_df[test_df["split"] == split_name]
        if num_labels == 2:
            texts = sub["prompt"].tolist()
            y_true = sub["label"].apply(lambda x: 1 if x == "malicious" else 0).tolist()
        else:
            sub = sub[sub["unified_label"].isin(MULTICLASS_LABEL_MAP)]
            texts = sub["prompt"].tolist()
            y_true = sub["unified_label"].map(MULTICLASS_LABEL_MAP).tolist()

        preds = []
        batch_size = 16
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            enc = tokenizer(batch_texts, padding=True, truncation=True, max_length=512, return_tensors="pt").to(device)
            with torch.no_grad():
                out = model(**enc)
                p = out.logits.argmax(-1).cpu().numpy()
                preds.extend(p)

        acc = accuracy_score(y_true, preds)
        p, r, f1, _ = precision_recall_fscore_support(y_true, preds, average=avg_type, zero_division=0)
        metrics.append({
            "model": f"DeBERTa ({task_name})",
            "split": split_name,
            "accuracy": round(acc, 4),
            "precision": round(p, 4),
            "recall": round(r, 4),
            "f1_score": round(f1, 4)
        })
        print(f"  [{split_name}] acc={acc:.4f} | precision={p:.4f} | recall={r:.4f} | f1={f1:.4f}")

    return metrics

def main():
    df = pd.read_csv(PROCESSED_DIR / "split_dataset.csv")
    df["prompt"] = df["prompt"].fillna("")

    all_metrics = []
    # 1. Binary
    b_metrics = evaluate_model_dir(MODELS_DIR / "binary", "binary", df, 2, "binary")
    all_metrics.extend(b_metrics)

    # 2. Multi-class
    mc_metrics = evaluate_model_dir(MODELS_DIR / "multiclass", "multiclass", df, 5, "macro")
    all_metrics.extend(mc_metrics)

    report_df = pd.DataFrame(all_metrics)
    report_path = REPORTS_DIR / "deberta_metrics.csv"
    report_df.to_csv(report_path, index=False)
    print(f"\nSaved DeBERTa metrics report to {report_path}")
    print(report_df.to_string(index=False))

if __name__ == "__main__":
    main()
