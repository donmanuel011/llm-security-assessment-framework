"""
Evaluation module for LLM Security Detection Subsystem.
Calculates comprehensive metrics (Accuracy, Precision, Recall, F1, FPR, FNR, ROC-AUC, Confusion Matrix).
"""

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    roc_auc_score
)

def calculate_detailed_metrics(y_true, y_pred, y_probs=None, class_names=None):
    """
    Computes standard and security-specific metrics (FPR, FNR, Macro/Weighted F1, ROC-AUC).
    """
    acc = accuracy_score(y_true, y_pred)
    
    # Per-class & overall precision, recall, f1
    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(y_true, y_pred, average="macro", zero_division=0)
    p_weighted, r_weighted, f1_weighted, _ = precision_recall_fscore_support(y_true, y_pred, average="weighted", zero_division=0)
    
    cm = confusion_matrix(y_true, y_pred)
    
    # Calculate binary FPR and FNR if binary classification
    fpr, fnr = 0.0, 0.0
    if cm.shape == (2, 2):
        tn, fp, fn, tp = cm.ravel()
        fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
        fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0
    
    roc_auc = None
    if y_probs is not None:
        try:
            if len(np.unique(y_true)) == 2:
                # Binary ROC-AUC using positive class probability
                pos_probs = y_probs[:, 1] if y_probs.ndim == 2 else y_probs
                roc_auc = float(roc_auc_score(y_true, pos_probs))
            else:
                # Multi-class ROC-AUC
                roc_auc = float(roc_auc_score(y_true, y_probs, multi_class="ovr"))
        except Exception:
            roc_auc = None

    metrics = {
        "accuracy": float(acc),
        "macro_precision": float(p_macro),
        "macro_recall": float(r_macro),
        "macro_f1": float(f1_macro),
        "weighted_f1": float(f1_weighted),
        "fpr": float(fpr),
        "fnr": float(fnr),
        "roc_auc": roc_auc,
        "confusion_matrix": cm.tolist()
    }
    
    # Add per-class details if class names supplied
    if class_names:
        p_class, r_class, f1_class, support = precision_recall_fscore_support(y_true, y_pred, average=None, zero_division=0)
        per_class_metrics = {}
        for i, c_name in enumerate(class_names):
            if i < len(p_class):
                per_class_metrics[c_name] = {
                    "precision": float(p_class[i]),
                    "recall": float(r_class[i]),
                    "f1": float(f1_class[i]),
                    "support": int(support[i])
                }
        metrics["per_class"] = per_class_metrics

    return metrics

def evaluate_models_on_dataset(test_df, model_predictions):
    """
    Evaluates multiple models on given test dataframe and returns a summary DataFrame.
    """
    rows = []
    for model_name, preds_dict in model_predictions.items():
        y_true = test_df["target"].values
        y_pred = preds_dict["pred"]
        y_probs = preds_dict.get("probs", None)

        m = calculate_detailed_metrics(y_true, y_pred, y_probs)
        rows.append({
            "model": model_name,
            "accuracy": round(m["accuracy"], 4),
            "macro_f1": round(m["macro_f1"], 4),
            "weighted_f1": round(m["weighted_f1"], 4),
            "fpr": round(m["fpr"], 4),
            "fnr": round(m["fnr"], 4),
            "roc_auc": round(m["roc_auc"], 4) if m["roc_auc"] is not None else "N/A"
        })

    return pd.DataFrame(rows)
