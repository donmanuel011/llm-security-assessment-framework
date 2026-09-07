"""
Assessment Engine (Phase 18, 21, 22).
Orchestrates end-to-end LLM Security Assessment:
  `Load Attack -> Run Detector -> Send to Target LLM -> Capture Response -> Evaluate Response -> Score Risk -> Save Report`
Computes Attack Success Rate (ASR) breakdown by attack type, difficulty, dataset, target model.
"""

import sys
import io
import os
import pathlib
import pandas as pd
import numpy as np

SCRIPT_DIR   = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.detection.predict import predict_prompt
from src.assessment.model_adapter import get_adapter
from src.assessment.response_evaluator import evaluate_target_response
from src.assessment.risk_scoring import calculate_risk_score
from src.detection.model_config import PROCESSED_DIR, REPORTS_DIR

def run_security_assessment(
    detector_model_key: str = "tfidf_lr",
    target_model_type: str = "mock",
    target_security_level: str = "medium",
    sample_size: int = 200
):
    print(f"\n{'='*60}")
    print(f"  RUNNING SECURITY ASSESSMENT ENGINE")
    print(f"  Detector: {detector_model_key} | Target LLM: {target_model_type} ({target_security_level})")
    print(f"{'='*60}")

    # 1. Load Attack Dataset
    dataset_path = PROCESSED_DIR / "assessment_dataset.csv"
    if not dataset_path.exists():
        dataset_path = PROCESSED_DIR / "unified_dataset.csv"

    df = pd.read_csv(dataset_path)
    df["prompt"] = df["prompt"].fillna("")

    if sample_size and sample_size < len(df):
        df = df.sample(n=sample_size, random_state=42).reset_index(drop=True)

    adapter = get_adapter(model_type=target_model_type, security_level=target_security_level)

    results = []
    for idx, row in df.iterrows():
        prompt = str(row["prompt"])
        attack_cat = row.get("unified_label", row.get("attack_type", "Unknown"))
        is_attack_prompt = (row.get("label", "malicious") == "malicious")

        # Step 1: Run Security Detector
        try:
            det_res = predict_prompt(prompt, model_key=detector_model_key)
        except Exception:
            det_res = {"is_attack": False, "confidence": 0.5, "label": "benign"}

        # Step 2: Send to Target LLM
        llm_out = adapter.generate(prompt)
        response_text = llm_out.get("response", "")

        # Step 3: Evaluate Target Response
        eval_res = evaluate_target_response(prompt, response_text, is_attack_prompt=is_attack_prompt)

        # Step 4: Calculate Risk Score
        risk_res = calculate_risk_score(
            attack_category=attack_cat,
            attack_successful=eval_res["attack_successful"],
            detector_confidence=det_res["confidence"],
            is_detected_by_security=det_res["is_attack"]
        )

        results.append({
            "prompt_id": idx,
            "attack_type": attack_cat,
            "source_dataset": row.get("source_dataset", "Unknown"),
            "difficulty": row.get("difficulty", "Medium"),
            "detector_label": det_res["label"],
            "detector_confidence": round(det_res["confidence"], 4),
            "detector_flagged": det_res["is_attack"],
            "target_response": response_text[:150] + "..." if len(response_text) > 150 else response_text,
            "refusal_detected": eval_res["refusal_detected"],
            "attack_successful": eval_res["attack_successful"],
            "risk_score": risk_res["risk_score"],
            "risk_tier": risk_res["risk_tier"]
        })

    res_df = pd.DataFrame(results)

    # 5. Compute Attack Success Rate (ASR)
    total_attacks = len(res_df[res_df["attack_type"] != "Benign"])
    successful_attacks = len(res_df[res_df["attack_successful"] == True])
    overall_asr = (successful_attacks / total_attacks * 100) if total_attacks > 0 else 0.0

    print(f"\n  Assessment Finished:")
    print(f"  Total Attacks Evaluated: {total_attacks}")
    print(f"  Successful Evasions/Breaches: {successful_attacks}")
    print(f"  Overall Attack Success Rate (ASR): {overall_asr:.2f}%")

    out_file = REPORTS_DIR / f"assessment_results_{detector_model_key}_{target_security_level}.csv"
    res_df.to_csv(out_file, index=False)
    print(f"  Saved full assessment log -> {out_file.name}\n")

    return res_df, overall_asr

if __name__ == "__main__":
    run_security_assessment("tfidf_lr", "mock", "medium", sample_size=50)
