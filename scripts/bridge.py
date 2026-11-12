"""
Bridge script between Node.js dashboard server and Python security framework.
Emits clean JSON output to stdout.
"""

import sys
import os
import json
import argparse
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.assessment.preflight_scanner import PreflightScanner
from src.assessment.risk_scoring import calculate_risk_score

def handle_detect(args):
    prompt = args.prompt or ""
    model = args.model or "tfidf_lr"
    
    # 1. Preflight check
    scanner = PreflightScanner()
    preflight = scanner.scan(prompt)
    entropy = scanner.shannon_entropy(prompt)
    
    result = {
        "prompt": prompt,
        "model_requested": model,
        "preflight": {
            "flagged": preflight["flagged"],
            "reason": preflight["reason"],
            "risk_multiplier": preflight["risk_multiplier"],
            "entropy": round(entropy, 3)
        },
        "ml_detection": None,
        "is_attack": preflight["flagged"],
        "label": preflight["reason"] if preflight["flagged"] else "benign",
        "confidence": 0.99 if preflight["flagged"] else 0.5
    }
    
    # 2. ML Detector attempt
    try:
        from src.detection.predict import predict_prompt
        ml_res = predict_prompt(prompt, model_key=model)
        result["ml_detection"] = ml_res
        if not preflight["flagged"]:
            result["is_attack"] = ml_res["is_attack"]
            result["label"] = ml_res["label"]
            result["confidence"] = ml_res["confidence"]
    except Exception as e:
        result["ml_detection_error"] = str(e)
        if not preflight["flagged"]:
            result["label"] = "benign (heuristic passed)"
            result["confidence"] = 0.85
            result["is_attack"] = False
            
    print(json.dumps(result))

def handle_assess(args):
    from src.assessment.assessment_engine import run_security_assessment
    # Suppress verbose stdout from assessment engine during JSON bridge mode
    import io
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        df, asr = run_security_assessment(
            detector_model_key=args.detector,
            target_model_type=args.target,
            target_model_name=args.model,
            target_security_level=args.security,
            sample_size=args.sample_size,
            api_key=args.api_key
        )
        sys.stdout = old_stdout
        
        # Prepare serializable results
        records = []
        if df is not None and not df.empty:
            for _, r in df.iterrows():
                records.append({
                    "prompt_id": str(r.get("prompt_id", "")),
                    "prompt": str(r.get("prompt", ""))[:120],
                    "attack_type": str(r.get("attack_type", "Unknown")),
                    "detector_flag": bool(r.get("detector_flagged", False)),
                    "attack_successful": bool(r.get("attack_successful", False)),
                    "refusal_detected": bool(r.get("refusal_detected", False)),
                    "risk_tier": str(r.get("risk_tier", "LOW")),
                    "risk_score": float(r.get("risk_score", 0.0)),
                    "model_response": str(r.get("target_response", ""))[:150]
                })
        
        out = {
            "status": "success",
            "sample_size": len(records),
            "asr": round(asr, 2),
            "refusal_rate": round(100.0 - asr, 2),
            "target": args.target,
            "security_level": args.security,
            "detector": args.detector,
            "records": records
        }
        print(json.dumps(out))
    except Exception as e:
        sys.stdout = old_stdout
        print(json.dumps({"status": "error", "error": str(e)}))

def handle_risk(args):
    res = calculate_risk_score(
        attack_category=args.category,
        attack_successful=args.successful,
        detector_confidence=args.confidence,
        is_detected_by_security=args.detected
    )
    print(json.dumps(res))

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    
    p_det = sub.add_parser("detect")
    p_det.add_argument("--prompt", required=True)
    p_det.add_argument("--model", default="tfidf_lr")
    
    p_ass = sub.add_parser("assess")
    p_ass.add_argument("--target", default="mock")
    p_ass.add_argument("--model", default=None)
    p_ass.add_argument("--security", default="medium")
    p_ass.add_argument("--sample-size", type=int, default=20)
    p_ass.add_argument("--detector", default="tfidf_lr")
    p_ass.add_argument("--api-key", default=None)
    
    p_rsk = sub.add_parser("risk")
    p_rsk.add_argument("--category", default="Jailbreak")
    p_rsk.add_argument("--successful", type=lambda x: str(x).lower() == 'true', default=True)
    p_rsk.add_argument("--confidence", type=float, default=0.8)
    p_rsk.add_argument("--detected", type=lambda x: str(x).lower() == 'true', default=True)
    
    args = parser.parse_args()
    if args.cmd == "detect":
        handle_detect(args)
    elif args.cmd == "assess":
        handle_assess(args)
    elif args.cmd == "risk":
        handle_risk(args)
    else:
        print(json.dumps({"error": "Unknown command"}))

if __name__ == "__main__":
    main()
