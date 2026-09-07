"""
Training Orchestrator for LLM Security Detection Subsystem (Phase 15).
Trains and persists:
  1. TF-IDF + Logistic Regression (joblib in models/tfidf_lr)
  2. TF-IDF + Linear SVM (joblib in models/tfidf_svm)
"""

import sys
import io
import os
import ssl
import pathlib
import joblib
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

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC

from src.detection.model_config import (
    PROCESSED_DIR,
    MODELS_DIR,
    REPORTS_DIR,
    MODEL_CONFIGS,
    MULTICLASS_LABEL_MAP
)

def banner(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def load_data():
    df = pd.read_csv(PROCESSED_DIR / "split_dataset.csv")
    df["prompt"] = df["prompt"].fillna("")
    df["target"] = df["label"].apply(lambda x: 1 if x == "malicious" else 0)
    df["target_multiclass"] = df["unified_label"].map(MULTICLASS_LABEL_MAP)
    return df

def train_and_save_sklearn():
    banner("Training Scikit-Learn Baselines & Persistence")
    df = load_data()
    train_df = df[df["split"] == "train"]

    X_train = train_df["prompt"].tolist()
    y_train = train_df["target"].tolist()

    vectorizer = TfidfVectorizer(max_features=10000, ngram_range=(1, 2))
    X_train_vec = vectorizer.fit_transform(X_train)

    # 1. TF-IDF + Logistic Regression
    lr_dir = MODELS_DIR / "tfidf_lr"
    lr_dir.mkdir(parents=True, exist_ok=True)
    print(f"Fitting Logistic Regression model...")
    lr_model = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
    lr_model.fit(X_train_vec, y_train)

    joblib.dump(lr_model, lr_dir / "model.joblib")
    joblib.dump(vectorizer, lr_dir / "tfidf.joblib")
    print(f"Saved TF-IDF LR model & vectorizer to {lr_dir}")

    # 2. TF-IDF + Linear SVM
    svm_dir = MODELS_DIR / "tfidf_svm"
    svm_dir.mkdir(parents=True, exist_ok=True)
    print(f"Fitting Linear SVM model...")
    svm_model = LinearSVC(C=1.0, random_state=42)
    svm_model.fit(X_train_vec, y_train)

    joblib.dump(svm_model, svm_dir / "model.joblib")
    joblib.dump(vectorizer, svm_dir / "tfidf.joblib")
    print(f"Saved TF-IDF SVM model & vectorizer to {svm_dir}")

def main():
    print("Starting Detection Infrastructure Training Pipeline...")
    train_and_save_sklearn()
    print("Scikit-Learn baseline models successfully trained & saved to models/ directory.")

if __name__ == "__main__":
    main()
