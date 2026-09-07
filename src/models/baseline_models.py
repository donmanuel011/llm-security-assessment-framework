"""
Phase 13 -- Baseline Models
=============================
Trains and evaluates 3 baseline models on the split dataset:
  1. TF-IDF + Logistic Regression
  2. TF-IDF + SVM
  3. DistilBERT fine-tuned classifier

Evaluation happens on:
  - test_known (known attacks test set)
  - test_novel (unseen attacks test set)
Outputs metrics to reports/baseline_metrics.csv
"""

import sys
import io
import os
import ssl
import pathlib
import pandas as pd
import numpy as np

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

# UTF-8 stdout
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from datasets import Dataset

SCRIPT_DIR    = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT  = SCRIPT_DIR.parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR   = PROJECT_ROOT / "reports"
MODELS_DIR    = PROJECT_ROOT / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

def banner(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def load_data():
    df = pd.read_csv(PROCESSED_DIR / "split_dataset.csv")
    df["prompt"] = df["prompt"].fillna("")
    # Binary classification: benign=0, malicious=1
    df["target"] = df["label"].apply(lambda x: 1 if x == "malicious" else 0)
    return df

def get_split(df, split_name):
    sub = df[df["split"] == split_name]
    return sub["prompt"].tolist(), sub["target"].tolist()

def evaluate_model(y_true, y_pred, model_name, split_name):
    acc = accuracy_score(y_true, y_pred)
    p, r, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="binary", zero_division=0)
    return {
        "model": model_name,
        "split": split_name,
        "accuracy": acc,
        "precision": p,
        "recall": r,
        "f1_score": f1
    }

def train_sklearn_baseline(model, name, X_train, y_train, X_known, y_known, X_novel, y_novel):
    print(f"  Training {name}...")
    model.fit(X_train, y_train)
    
    metrics = []
    # Test Known
    pred_known = model.predict(X_known)
    metrics.append(evaluate_model(y_known, pred_known, name, "test_known"))
    
    # Test Novel
    pred_novel = model.predict(X_novel)
    metrics.append(evaluate_model(y_novel, pred_novel, name, "test_novel"))
    
    return metrics

def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    p, r, f1, _ = precision_recall_fscore_support(labels, preds, average="binary", zero_division=0)
    acc = accuracy_score(labels, preds)
    return {"accuracy": acc, "f1": f1, "precision": p, "recall": r}

def train_bert_baseline(train_texts, train_labels, val_texts, val_labels, known_texts, known_labels, novel_texts, novel_labels):
    name = "DistilBERT"
    print(f"  Training {name}...")
    
    model_id = "distilbert-base-uncased"
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForSequenceClassification.from_pretrained(model_id, num_labels=2)
    
    def tokenize(texts):
        return tokenizer(texts, padding=True, truncation=True, max_length=512)
    
    train_enc = tokenize(train_texts)
    val_enc = tokenize(val_texts)
    known_enc = tokenize(known_texts)
    novel_enc = tokenize(novel_texts)
    
    class SimpleDataset(torch.utils.data.Dataset):
        def __init__(self, encodings, labels):
            self.encodings = encodings
            self.labels = labels
        def __getitem__(self, idx):
            item = {k: torch.tensor(v[idx]) for k, v in self.encodings.items()}
            item["labels"] = torch.tensor(self.labels[idx])
            return item
        def __len__(self):
            return len(self.labels)
            
    train_dataset = SimpleDataset(train_enc, train_labels)
    val_dataset = SimpleDataset(val_enc, val_labels)
    known_dataset = SimpleDataset(known_enc, known_labels)
    novel_dataset = SimpleDataset(novel_enc, novel_labels)
    
    training_args = TrainingArguments(
        output_dir=str(MODELS_DIR / "distilbert_baseline"),
        num_train_epochs=3,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=32,
        warmup_steps=100,
        weight_decay=0.01,
        logging_steps=10,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        report_to="none"
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics
    )
    
    trainer.train()
    
    # Evaluate
    metrics = []
    
    pred_known = trainer.predict(known_dataset)
    pred_classes = pred_known.predictions.argmax(-1)
    metrics.append(evaluate_model(known_labels, pred_classes, name, "test_known"))
    
    pred_novel = trainer.predict(novel_dataset)
    pred_classes = pred_novel.predictions.argmax(-1)
    metrics.append(evaluate_model(novel_labels, pred_classes, name, "test_novel"))
    
    return metrics

def main():
    banner("Phase 13 -- Baseline Models")
    df = load_data()
    
    train_texts, train_labels = get_split(df, "train")
    val_texts, val_labels = get_split(df, "val")
    known_texts, known_labels = get_split(df, "test_known")
    novel_texts, novel_labels = get_split(df, "test_novel")
    
    print(f"  Train: {len(train_texts)} | Val: {len(val_texts)} | Known: {len(known_texts)} | Novel: {len(novel_texts)}")
    
    all_metrics = []
    
    # TF-IDF Setup
    print("\n  Extracting TF-IDF features...")
    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
    X_train = vectorizer.fit_transform(train_texts)
    X_known = vectorizer.transform(known_texts)
    X_novel = vectorizer.transform(novel_texts)
    
    # Baseline 1: TF-IDF + LR
    lr = LogisticRegression(max_iter=1000)
    all_metrics.extend(train_sklearn_baseline(lr, "TF-IDF + LR", X_train, train_labels, X_known, known_labels, X_novel, novel_labels))
    
    # Baseline 2: TF-IDF + SVM
    svm = LinearSVC(max_iter=2000)
    all_metrics.extend(train_sklearn_baseline(svm, "TF-IDF + SVM", X_train, train_labels, X_known, known_labels, X_novel, novel_labels))
    
    # Baseline 3: DistilBERT
    all_metrics.extend(train_bert_baseline(
        train_texts, train_labels, 
        val_texts, val_labels, 
        known_texts, known_labels, 
        novel_texts, novel_labels
    ))
    
    metrics_df = pd.DataFrame(all_metrics)
    
    banner("Final Metrics")
    print(metrics_df.to_string(index=False))
    
    out_path = REPORTS_DIR / "baseline_metrics.csv"
    metrics_df.to_csv(out_path, index=False)
    print(f"\n  [+] Saved baseline metrics -> {out_path.name}")
    print(f"\n{'#'*60}")
    print(f"  PHASE 13 COMPLETE [OK]")
    print(f"{'#'*60}\n")

if __name__ == "__main__":
    main()
