"""
Model Configuration and Constants for Detection Subsystem
"""

import pathlib

SCRIPT_DIR   = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Paths
DATA_DIR      = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR    = PROJECT_ROOT / "models"
REPORTS_DIR   = PROJECT_ROOT / "reports"

# Ensure directories exist
MODELS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Binary Labels
BINARY_LABELS = {0: "benign", 1: "malicious"}
BINARY_LABEL_MAP = {"benign": 0, "malicious": 1}

# Multi-class Labels (5 classes)
MULTICLASS_LABEL_MAP = {
    "Benign": 0,
    "Prompt Injection": 1,
    "Indirect Prompt Injection": 2,
    "Jailbreak": 3,
    "Prompt Leakage": 4,
}
MULTICLASS_ID_TO_LABEL = {v: k for k, v in MULTICLASS_LABEL_MAP.items()}

# Model Hyperparameters and Identifiers
MODEL_CONFIGS = {
    "tfidf_lr": {
        "name": "TF-IDF + Logistic Regression",
        "type": "sklearn",
        "max_features": 10000,
        "ngram_range": (1, 2),
        "c_param": 1.0,
        "save_dir": MODELS_DIR / "tfidf_lr"
    },
    "tfidf_svm": {
        "name": "TF-IDF + Linear SVM",
        "type": "sklearn",
        "max_features": 10000,
        "ngram_range": (1, 2),
        "c_param": 1.0,
        "save_dir": MODELS_DIR / "tfidf_svm"
    },
    "distilbert": {
        "name": "DistilBERT Baseline",
        "type": "transformer",
        "pretrained_model": "distilbert-base-uncased",
        "max_length": 512,
        "batch_size": 16,
        "epochs": 3,
        "lr": 2e-5,
        "save_dir": MODELS_DIR / "distilbert_baseline"
    },
    "deberta_binary": {
        "name": "DeBERTa-v3 Binary Classifier",
        "type": "transformer",
        "pretrained_model": "microsoft/deberta-v3-base",
        "max_length": 512,
        "batch_size": 8,
        "epochs": 3,
        "lr": 2e-5,
        "save_dir": MODELS_DIR / "deberta" / "binary"
    },
    "deberta_multiclass": {
        "name": "DeBERTa-v3 Multi-class Classifier",
        "type": "transformer",
        "pretrained_model": "microsoft/deberta-v3-base",
        "max_length": 512,
        "batch_size": 8,
        "epochs": 3,
        "lr": 2e-5,
        "save_dir": MODELS_DIR / "deberta" / "multiclass"
    }
}
