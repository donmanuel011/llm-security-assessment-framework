"""
Phase 14 -- DeBERTa Detector
==============================
Trains two classifiers on top of microsoft/deberta-v3-base:

  1. Binary Classifier:
       - Benign  (0)
       - Attack  (1)

  2. Multi-class Classifier (5 classes):
       - Benign               (0)
       - Prompt Injection     (1)
       - Indirect Prompt Injection (2)
       - Jailbreak            (3)
       - Prompt Leakage       (4)

Models are saved to models/deberta/binary/ and models/deberta/multiclass/
Metrics are saved to reports/deberta_metrics.csv
"""

import sys
import io
import os
import ssl
import pathlib
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report

# SSL / HF patches (must be BEFORE transformers imports)
os.environ["HF_HUB_DISABLE_SSL_VERIFICATION"] = "1"
os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""
ssl._create_default_https_context = ssl._create_unverified_context

import httpx
_orig_httpx_init = httpx.Client.__init__
def _patched_httpx_init(self, *args, **kwargs):
    kwargs["verify"] = False
    _orig_httpx_init(self, *args, **kwargs)
httpx.Client.__init__ = _patched_httpx_init

# UTF-8 stdout
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
    DataCollatorWithPadding,
)

SCRIPT_DIR    = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT  = SCRIPT_DIR.parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR    = PROJECT_ROOT / "models" / "deberta"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR   = PROJECT_ROOT / "reports"

MODEL_ID = "microsoft/deberta-v3-base"

# ── Label maps ────────────────────────────────────────────────────────────────
BINARY_LABEL_MAP = {
    "benign":   0,
    "malicious": 1,
}

MULTICLASS_LABEL_MAP = {
    "Benign":                    0,
    "Prompt Injection":          1,
    "Indirect Prompt Injection": 2,
    "Jailbreak":                 3,
    "Prompt Leakage":            4,
}
MULTICLASS_NAMES = {v: k for k, v in MULTICLASS_LABEL_MAP.items()}

def banner(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ── Dataset class ─────────────────────────────────────────────────────────────
class PromptDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels    = labels

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        item = {k: torch.tensor(v[idx]) for k, v in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[idx])
        return item


# ── Tokenize ──────────────────────────────────────────────────────────────────
def tokenize_texts(tokenizer, texts):
    return tokenizer(
        texts, padding=True, truncation=True, max_length=512, return_tensors=None
    )


# ── Metrics ───────────────────────────────────────────────────────────────────
def compute_metrics_binary(pred):
    labels = pred.label_ids
    preds  = pred.predictions.argmax(-1)
    p, r, f1, _ = precision_recall_fscore_support(labels, preds, average="binary", zero_division=0)
    acc = accuracy_score(labels, preds)
    return {"accuracy": acc, "f1": f1, "precision": p, "recall": r}


def compute_metrics_multiclass(pred):
    labels = pred.label_ids
    preds  = pred.predictions.argmax(-1)
    p, r, f1, _ = precision_recall_fscore_support(labels, preds, average="macro", zero_division=0)
    acc = accuracy_score(labels, preds)
    return {"accuracy": acc, "f1_macro": f1, "precision_macro": p, "recall_macro": r}


# ── Training helper ──────────────────────────────────────────────────────────
def train_and_evaluate(
    task_name, num_labels, compute_metrics_fn, label_map,
    train_texts, train_labels,
    val_texts, val_labels,
    known_texts, known_labels,
    novel_texts, novel_labels,
    tokenizer, epochs=3
):
    print(f"\n  Loading {MODEL_ID} for {task_name} ({num_labels} classes)...")
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID, num_labels=num_labels)

    enc_train = tokenize_texts(tokenizer, train_texts)
    enc_val   = tokenize_texts(tokenizer, val_texts)
    enc_known = tokenize_texts(tokenizer, known_texts)
    enc_novel = tokenize_texts(tokenizer, novel_texts)

    ds_train = PromptDataset(enc_train, train_labels)
    ds_val   = PromptDataset(enc_val,   val_labels)
    ds_known = PromptDataset(enc_known, known_labels)
    ds_novel = PromptDataset(enc_novel, novel_labels)

    save_dir = str(MODELS_DIR / task_name)
    args = TrainingArguments(
        output_dir=save_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=16,
        learning_rate=1e-5,
        max_grad_norm=1.0,
        fp16=False,
        bf16=False,
        warmup_steps=100,
        weight_decay=0.01,
        logging_steps=20,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1" if num_labels == 2 else "f1_macro",
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=ds_train,
        eval_dataset=ds_val,
        compute_metrics=compute_metrics_fn,
        data_collator=DataCollatorWithPadding(tokenizer),
    )

    trainer.train()
    trainer.save_model(save_dir)
    tokenizer.save_pretrained(save_dir)
    print(f"  [+] Saved model to models/deberta/{task_name}/")

    # Evaluate
    metrics = []
    for split_name, ds, y_true in [
        ("test_known", ds_known, known_labels),
        ("test_novel", ds_novel, novel_labels),
    ]:
        pred_out   = trainer.predict(ds)
        pred_class = pred_out.predictions.argmax(-1)
        acc = accuracy_score(y_true, pred_class)
        avg = "binary" if num_labels == 2 else "macro"
        p, r, f1, _ = precision_recall_fscore_support(y_true, pred_class, average=avg, zero_division=0)
        metrics.append({
            "model": f"DeBERTa ({task_name})",
            "split": split_name,
            "accuracy": round(acc, 4),
            "precision": round(p, 4),
            "recall": round(r, 4),
            "f1_score": round(f1, 4),
        })
        print(f"\n  [{split_name}] acc={acc:.4f} | precision={p:.4f} | recall={r:.4f} | f1={f1:.4f}")

        # Per-class report for multi-class
        if num_labels > 2:
            print(f"\n  Per-class report [{split_name}]:")
            target_names = [MULTICLASS_NAMES[i] for i in sorted(MULTICLASS_NAMES)]
            print(classification_report(y_true, pred_class, target_names=target_names, zero_division=0))

    return metrics


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print(f"\n{'#'*60}")
    print(f"  PHASE 14 -- DeBERTa DETECTOR")
    print(f"{'#'*60}")

    # Load detector dataset (binary) and split dataset (multi-class)
    detector_path = PROCESSED_DIR / "split_dataset.csv"
    if not detector_path.exists():
        print(f"  [ERROR] split_dataset.csv not found!")
        return

    df = pd.read_csv(detector_path)
    df["prompt"] = df["prompt"].fillna("")
    print(f"  Loaded {len(df):,} rows from split_dataset.csv")

    def get_split(split_name):
        return df[df["split"] == split_name]

    banner("Loading tokenizer")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    print(f"  Tokenizer loaded: {MODEL_ID}")

    all_metrics = []

    # ── Task 1: Binary ────────────────────────────────────────────────────────
    banner("Task 1: Binary Classifier (Benign vs. Attack)")

    def get_binary(split_name):
        s = get_split(split_name)
        texts  = s["prompt"].tolist()
        labels = s["label"].apply(lambda x: 1 if x == "malicious" else 0).tolist()
        return texts, labels

    tr_t, tr_l = get_binary("train")
    va_t, va_l = get_binary("val")
    kn_t, kn_l = get_binary("test_known")
    nv_t, nv_l = get_binary("test_novel")

    binary_metrics = train_and_evaluate(
        "binary", 2, compute_metrics_binary, BINARY_LABEL_MAP,
        tr_t, tr_l, va_t, va_l, kn_t, kn_l, nv_t, nv_l,
        tokenizer, epochs=3
    )
    all_metrics.extend(binary_metrics)

    # ── Task 2: Multi-class ───────────────────────────────────────────────────
    banner("Task 2: Multi-class Classifier (5 classes)")

    def get_multiclass(split_name):
        s = get_split(split_name)
        # Drop rows whose unified_label isn't in our label map
        s = s[s["unified_label"].isin(MULTICLASS_LABEL_MAP)]
        texts  = s["prompt"].tolist()
        labels = s["unified_label"].map(MULTICLASS_LABEL_MAP).tolist()
        return texts, labels

    tr_t, tr_l = get_multiclass("train")
    va_t, va_l = get_multiclass("val")
    kn_t, kn_l = get_multiclass("test_known")
    nv_t, nv_l = get_multiclass("test_novel")

    mc_metrics = train_and_evaluate(
        "multiclass", 5, compute_metrics_multiclass, MULTICLASS_LABEL_MAP,
        tr_t, tr_l, va_t, va_l, kn_t, kn_l, nv_t, nv_l,
        tokenizer, epochs=3
    )
    all_metrics.extend(mc_metrics)

    # ── Save report ───────────────────────────────────────────────────────────
    banner("Final Results")
    report_df = pd.DataFrame(all_metrics)
    print(report_df.to_string(index=False))

    report_path = REPORTS_DIR / "deberta_metrics.csv"
    report_df.to_csv(report_path, index=False)
    print(f"\n  [+] Saved DeBERTa metrics -> {report_path.name}")

    print(f"\n{'#'*60}")
    print(f"  PHASE 14 COMPLETE [OK]")
    print(f"{'#'*60}\n")


if __name__ == "__main__":
    main()
