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
from src.assessment.preflight_scanner import PreflightScanner
from src.detection.model_config import PROCESSED_DIR, REPORTS_DIR

def run_security_assessment(
    detector_model_key: str = "tfidf_lr",
    target_model_type: str = "mock",
    target_model_name: str = None,
    target_security_level: str = "medium",
    sample_size: int = 200,
    api_key: str = None,
    api_base: str = None,
    custom_config: str = None
):
    print(f"\n{'='*60}")
    print(f"  RUNNING SECURITY ASSESSMENT ENGINE")
    model_label = target_model_name or target_model_type
    print(f"  Detector: {detector_model_key} (+ Preflight) | Target LLM: {model_label} ({target_security_level})")
    print(f"{'='*60}")

    # 1. Load Attack Dataset
    dataset_path = PROCESSED_DIR / "assessment_dataset.csv"
    if not dataset_path.exists():
        dataset_path = PROCESSED_DIR / "unified_dataset.csv"

    df = pd.read_csv(dataset_path)
    df["prompt"] = df["prompt"].fillna("")

    if sample_size and sample_size < len(df):
        df = df.sample(n=sample_size, random_state=42).reset_index(drop=True)

    adapter = get_adapter(model_type=target_model_type, model_name=target_model_name, security_level=target_security_level, api_key=api_key, api_base=api_base, custom_config=custom_config)
    preflight = PreflightScanner()

    results = []
    total_rows = len(df)

    # -- Live prompt-by-prompt display header ------------------------------------
    print(f"\n  {'#':>4}  {'Attack Type':<28} {'Det':^5} {'Outcome':<12} {'Risk':<8}  Prompt Preview")
    print(f"  {'-'*4}  {'-'*28} {'-'*5} {'-'*12} {'-'*8}  {'-'*40}")

    for enum_idx, (idx, row) in enumerate(df.iterrows(), start=1):
        prompt = str(row["prompt"])
        attack_cat = row.get("unified_label", row.get("attack_type", "Unknown"))
        is_attack_prompt = (row.get("label", "malicious") == "malicious")

        # Step 1: Run Preflight Heuristic Scanner (Early Detection)
        preflight_res = preflight.scan(prompt)
        
        if preflight_res["flagged"]:
            det_res = {
                "is_attack": True, 
                "confidence": 0.99, 
                "label": preflight_res["reason"]
            }
        else:
            # Step 1b: Run Heavy Security Detector if Preflight passes
            try:
                det_res = predict_prompt(prompt, model_key=detector_model_key)
            except Exception:
                det_res = {"is_attack": False, "confidence": 0.5, "label": "benign"}

        # Step 2: Send to Target LLM
        llm_out = adapter.generate(prompt)
        
        if llm_out.get("status") == "error":
            print(f"\n\n[!] CRITICAL ERROR FROM MODEL ADAPTER:")
            print(f"    {llm_out.get('response', 'Unknown Error')}")
            print("\n[!] Aborting assessment.")
            sys.exit(1)
            
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

        # -- Live per-prompt status line -----------------------------------------
        det_flag  = "[Y]" if det_res["is_attack"] else "[ ]"
        if eval_res["attack_successful"]:
            outcome   = "[X] BREACHED"
        elif eval_res["refusal_detected"]:
            outcome   = "[Y] BLOCKED "
        else:
            outcome   = "    BENIGN  "
        risk_tier = risk_res["risk_tier"]
        prompt_preview = prompt.replace("\n", " ")[:42].encode("ascii", "ignore").decode("ascii")
        cat_short = str(attack_cat)[:28].encode("ascii", "ignore").decode("ascii")
        print(f"  {enum_idx:>4}/{total_rows:<4} {cat_short:<28} {det_flag:^5} {outcome:<12} {risk_tier:<8}  {prompt_preview}")

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
            "risk_tier": risk_res["risk_tier"],
            "is_malicious": is_attack_prompt
        })

    res_df = pd.DataFrame(results)

    # 5. Compute Attack Success Rate (ASR) and False Positive Rate (FPR)
    total_attacks = len(res_df[res_df["is_malicious"] == True])
    successful_attacks = len(res_df[(res_df["is_malicious"] == True) & (res_df["attack_successful"] == True)])
    overall_asr = (successful_attacks / total_attacks * 100) if total_attacks > 0 else 0.0

    total_benign = len(res_df[res_df["is_malicious"] == False])
    blocked_benign = len(res_df[(res_df["is_malicious"] == False) & (res_df["refusal_detected"] == True)])
    overall_fpr = (blocked_benign / total_benign * 100) if total_benign > 0 else 0.0

    print(f"\n  {'='*70}")
    print(f"  ASSESSMENT COMPLETE")
    print(f"  {'-'*70}")
    print(f"  Total Prompts Tested    : {len(res_df)}")
    print(f"  Total Attacks Evaluated : {total_attacks}")
    print(f"  Successful Breaches     : {successful_attacks}")
    print(f"  Overall ASR (Attacks)   : {overall_asr:.2f}%")
    print(f"  Benign Prompts Blocked  : {blocked_benign} / {total_benign}")
    print(f"  False Positive Rate     : {overall_fpr:.2f}%")

    # ── Per-attack-type summary ──────────────────────────────────────────────
    if total_attacks > 0:
        print(f"\n  {'-'*50}")
        print(f"  {'Attack Type':<30} {'Tested':>6} {'Breached':>8} {'ASR':>7}")
        print(f"  {'-'*30} {'-'*6} {'-'*8} {'-'*7}")
        for atype, grp in res_df[res_df["is_malicious"] == True].groupby("attack_type"):
            t_count = len(grp)
            s_count = grp["attack_successful"].sum()
            asr_pct = (s_count / t_count * 100) if t_count > 0 else 0.0
            print(f"  {str(atype):<30} {t_count:>6} {s_count:>8} {asr_pct:>6.1f}%")
        print(f"  {'-'*50}")

    out_file = REPORTS_DIR / f"assessment_results_{detector_model_key}_{target_security_level}.csv"
    res_df.to_csv(out_file, index=False)
    print(f"\n  Report saved -> {out_file}\n")

    return res_df, overall_asr

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="LLM Security Assessment Engine")
    parser.add_argument("--target", type=str, default="mock", choices=["mock", "local", "api", "gemini", "groq", "ollama", "custom"],
                        help="Target LLM type: mock | local | gemini | api | groq | ollama | custom")
    parser.add_argument("--model", type=str, default=None,
                        help="Model name override (e.g. gemini-1.5-flash, TinyLlama/TinyLlama-1.1B-Chat-v1.0)")
    parser.add_argument("--api-key", type=str, default=None,
                        help="API key (or set GEMINI_API_KEY / OPENAI_API_KEY env var)")
    parser.add_argument("--api-base", type=str, default=None,
                        help="Base URL for OpenAI-compatible APIs or Ollama (e.g. http://localhost:11434)")
    parser.add_argument("--custom-config", type=str, default=None,
                        help="Path to JSON config file for custom REST API adapter")
    parser.add_argument("--security-level", type=str, default="medium", choices=["low", "medium", "high"],
                        help="Security posture for mock adapter only")
    parser.add_argument("--sample-size", type=int, default=50,
                        help="Number of prompts to test (default: 50)")
    parser.add_argument("--detector", type=str, default="tfidf_lr",
                        help="Detector model to use: tfidf_lr | tfidf_svm | deberta_binary | deberta_multiclass")
    args = parser.parse_args()

    run_security_assessment(
        detector_model_key=args.detector,
        target_model_type=args.target,
        target_model_name=args.model,
        target_security_level=args.security_level,
        sample_size=args.sample_size,
        api_key=args.api_key,
        api_base=args.api_base,
        custom_config=args.custom_config
    )
