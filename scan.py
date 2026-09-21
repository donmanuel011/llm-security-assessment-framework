#!/usr/bin/env python
"""
scan.py  - Quick LLM Security Scanner
======================================
Run from the project root with the venv active.

Basic usage (mock LLM, 20 prompts):
    python scan.py

Test against Gemini (needs GEMINI_API_KEY set):
    python scan.py -t gemini -n 30

All options:
    python scan.py --help
"""

import sys
import pathlib
import argparse

# ensure project root is on the path
ROOT = pathlib.Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.assessment.assessment_engine import run_security_assessment


def build_parser():
    p = argparse.ArgumentParser(
        prog="scan",
        description=(
            "LLM Security Scanner - tests a target LLM against adversarial prompts\n"
            "and reports Attack Success Rate (ASR) with per-prompt live output."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples
--------
  # Quick mock scan (offline, no API key needed)
  python scan.py

  # 50 prompts, HIGH security mock
  python scan.py -n 50 -s high

        # Scan Llama 3.3 70B via Groq (free key from console.groq.com)
  set GROQ_API_KEY=your_key
  python scan.py -t groq -n 25

  # Scan against Gemini (free tier key)
  set GEMINI_API_KEY=your_key
  python scan.py -t gemini -n 25

  # Scan against OpenAI GPT-3.5
  python scan.py -t api -m gpt-3.5-turbo --api-key sk-...

  # Use a different detector model
  python scan.py --detector tfidf_svm
        """,
    )
    p.add_argument("-t", "--target", default="mock",
                   choices=["mock", "local", "api", "gemini", "groq"], metavar="TARGET",
                   help="Target LLM: mock | local | api | gemini | groq  (default: mock)")
    p.add_argument("-m", "--model", default=None, metavar="MODEL",
                   help="Model name override (e.g. gemini-2.0-flash-lite, gpt-4o-mini)")
    p.add_argument("-n", "--num-prompts", dest="sample_size", type=int, default=20,
                   metavar="N", help="Number of prompts to test  (default: 20)")
    p.add_argument("-s", "--security-level", dest="security_level", default="medium",
                   choices=["low", "medium", "high"],
                   help="Mock LLM security posture: low | medium | high  (default: medium)")
    p.add_argument("-d", "--detector", default="tfidf_lr", metavar="DETECTOR",
                   help="Detector model key: tfidf_lr | tfidf_svm  (default: tfidf_lr)")
    p.add_argument("-k", "--api-key", dest="api_key", default=None, metavar="KEY",
                   help="API key for Groq/Gemini/OpenAI (or set GROQ_API_KEY / GEMINI_API_KEY / OPENAI_API_KEY)")
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  LLM SECURITY SCANNER")
    print("=" * 60)
    print(f"  Target  : {args.target}" + (f" ({args.model})" if args.model else ""))
    print(f"  Prompts : {args.sample_size}")
    print(f"  Security: {args.security_level}  |  Detector: {args.detector}")
    print("=" * 60)

    run_security_assessment(
        detector_model_key=args.detector,
        target_model_type=args.target,
        target_model_name=args.model,
        target_security_level=args.security_level,
        sample_size=args.sample_size,
        api_key=args.api_key,
    )


if __name__ == "__main__":
    main()
