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
    p.add_argument("-t", "--target", default="auto",
                   choices=["auto", "mock", "local", "api", "gemini", "groq", "ollama", "custom"], metavar="TARGET",
                   help="Target LLM: auto | mock | local | api | gemini | groq | ollama | custom  (default: auto)")
    p.add_argument("-m", "--model", default=None, metavar="MODEL",
                   help="Model name override (e.g. gemini-2.0-flash-lite, gpt-4o-mini)")
    p.add_argument("-n", "--num-prompts", dest="sample_size", type=int, default=20,
                   metavar="N", help="Number of prompts to test  (default: 20)")
    p.add_argument("-s", "--security-level", dest="security_level", default="medium",
                   choices=["low", "medium", "high"],
                   help="Mock LLM security posture: low | medium | high  (default: medium)")
    p.add_argument("-d", "--detector", default="deberta_binary", metavar="DETECTOR",
                   help="Detector model key: tfidf_lr | tfidf_svm | deberta_binary | deberta_multiclass (default: deberta_binary)")
    p.add_argument("-k", "--api-key", dest="api_key", default=None, metavar="KEY",
                   help="API key for Groq/Gemini/OpenAI (or set GROQ_API_KEY / GEMINI_API_KEY / OPENAI_API_KEY)")
    p.add_argument("--api-base", dest="api_base", default=None, metavar="URL",
                   help="Base URL for OpenAI-compatible APIs or Ollama (e.g. http://localhost:11434)")
    p.add_argument("--custom-config", dest="custom_config", default=None, metavar="FILE",
                   help="Path to JSON config file for custom REST API adapter")
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
        api_base=args.api_base,
        custom_config=args.custom_config,
    )


if __name__ == "__main__":
    main()
