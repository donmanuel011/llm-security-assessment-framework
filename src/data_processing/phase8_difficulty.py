"""
Phase 8 -- Difficulty Classification
======================================
Reads taxonomy-mapped datasets (taxmap_*.csv) from data/interim/ and
assigns a difficulty score (Easy / Medium / Hard / Novel) to each sample
using a rule-based heuristic scoring system.

Scoring dimensions (each contributes 0 or 1 point):
  1. Obfuscation level       -- encoded/obfuscated text detected
  2. Structural complexity   -- prompt is long and multi-part
  3. Multi-step chaining     -- numbered steps / instruction chains detected
  4. Context dependency      -- relies on prior context (from schema field)
  5. Indirect delivery       -- attack type is Indirect Prompt Injection
  6. Multi-turn nature       -- references prior conversation / turns
  7. Semantic subtlety       -- category suggests a subtle/ambiguous attack

Score -> Difficulty:
  0-1 : Easy
  2-3 : Medium
  4-5 : Hard
  6-7 : Novel

Outputs: data/interim/diffclass_*.csv
         reports/difficulty_report.csv
"""

import sys
import io
import re
import pathlib
import pandas as pd

# UTF-8 stdout
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR   = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
INTERIM_DIR  = PROJECT_ROOT / "data" / "interim"
REPORTS_DIR  = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Scoring helpers ────────────────────────────────────────────────────────────

# 1. Obfuscation level
_BASE64_PATTERN   = re.compile(r"[A-Za-z0-9+/]{20,}={0,2}")
_HEX_PATTERN      = re.compile(r"(0x[0-9a-fA-F]{4,}|\\x[0-9a-fA-F]{2})")
_LEET_CHARS       = set("@3!1|0$")
_UNICODE_BLOCK    = re.compile(r"[\u0400-\u04FF\u0600-\u06FF\u4E00-\u9FFF\u2580-\u259F]")
_URL_ENCODE       = re.compile(r"%[0-9A-Fa-f]{2}")
_EXCESSIVE_CAPS   = re.compile(r"[A-Z]{5,}")

def score_obfuscation(text: str) -> int:
    indicators = 0
    if _BASE64_PATTERN.search(text):    indicators += 1
    if _HEX_PATTERN.search(text):       indicators += 1
    if _URL_ENCODE.search(text):        indicators += 1
    if _UNICODE_BLOCK.search(text):     indicators += 1
    if len(set(text) & _LEET_CHARS) >= 3: indicators += 1
    if _EXCESSIVE_CAPS.search(text):    indicators += 1
    return 1 if indicators >= 1 else 0


# 2. Structural complexity (long + multiple paragraphs or sentences)
def score_structural_complexity(text: str) -> int:
    words = len(text.split())
    sentences = len(re.split(r"[.!?]+", text))
    paragraphs = len([p for p in text.split("\n\n") if p.strip()])
    # Complex if: long (>150 words) AND multi-sentence/paragraph
    if words > 150 and (sentences > 4 or paragraphs > 2):
        return 1
    return 0


# 3. Multi-step instruction chaining
_STEP_PATTERNS = [
    re.compile(r"(step\s*\d+|first[,:]|second[,:]|third[,:]|finally[,:])", re.I),
    re.compile(r"(\d+\.\s+\w|\d+\)\s+\w)"),       # numbered lists
    re.compile(r"(then|after that|next,|followed by)", re.I),
]

def score_multistep(text: str) -> int:
    hits = sum(1 for p in _STEP_PATTERNS if p.search(text))
    return 1 if hits >= 2 else 0


# 4. Context dependency (schema field)
def score_context_dependency(value) -> int:
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, str):
        return 1 if value.lower() in ("true", "1", "yes") else 0
    try:
        return 1 if bool(value) else 0
    except Exception:
        return 0


# 5. Indirect delivery method
def score_indirect(unified_label: str) -> int:
    return 1 if str(unified_label).strip() == "Indirect Prompt Injection" else 0


# 6. Multi-turn references
_MULTITURN_PATTERNS = re.compile(
    r"(previous (message|conversation|turn|response)|"
    r"as (i|we) (said|mentioned|discussed)|"
    r"remember (what|that|from)|"
    r"continuing (from|our)|"
    r"follow.up|"
    r"in the (last|prior) (message|turn|conversation))",
    re.I,
)

def score_multiturn(text: str) -> int:
    return 1 if _MULTITURN_PATTERNS.search(text) else 0


# 7. Semantic subtlety (based on subtype/category keywords)
_SUBTLE_KEYWORDS = {
    "role", "persona", "fictional", "hypothetical", "scenario",
    "research", "academic", "educational", "creative writing",
    "thought experiment", "alternative", "pretend", "simulate",
    "act as", "imagine", "story", "indirect", "subtle",
}

def score_semantic_subtlety(attack_subtype: str, prompt: str) -> int:
    combined = (str(attack_subtype) + " " + prompt).lower()
    hits = sum(1 for kw in _SUBTLE_KEYWORDS if kw in combined)
    return 1 if hits >= 2 else 0


# ── Difficulty assignment ──────────────────────────────────────────────────────

def compute_score(row: pd.Series) -> tuple[int, str]:
    text = str(row.get("prompt", ""))
    
    s1 = score_obfuscation(text)
    s2 = score_structural_complexity(text)
    s3 = score_multistep(text)
    s4 = score_context_dependency(row.get("context_dependency", False))
    s5 = score_indirect(str(row.get("unified_label", row.get("attack_type", ""))))
    s6 = score_multiturn(text)
    s7 = score_semantic_subtlety(str(row.get("attack_subtype", "")), text)
    
    total = s1 + s2 + s3 + s4 + s5 + s6 + s7

    if total <= 1:
        difficulty = "Easy"
    elif total <= 3:
        difficulty = "Medium"
    elif total <= 5:
        difficulty = "Hard"
    else:
        difficulty = "Novel"
    
    return total, difficulty


def banner(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


DATASET_CONFIG = [
    ("HarmBench",      "taxmap_harmbench.csv"),
    ("JailbreakBench", "taxmap_jailbreakbench.csv"),
    ("PIBench",        "taxmap_pibench.csv"),
    ("TensorTrust",    "taxmap_tensor_trust.csv"),
    ("Benign",         "taxmap_benign.csv"),
]


def process_dataset(name: str, fname: str) -> dict:
    input_path = INTERIM_DIR / fname
    if not input_path.exists():
        print(f"  [WARN] Missing: {fname} -- skipping.")
        return {}

    df = pd.read_csv(input_path)
    df["prompt"] = df["prompt"].fillna("")
    print(f"  Loaded {len(df)} rows from {fname}")

    scores_and_diffs = df.apply(compute_score, axis=1)
    df["difficulty_score"] = scores_and_diffs.apply(lambda x: x[0])
    df["difficulty"]       = scores_and_diffs.apply(lambda x: x[1])

    dist = df["difficulty"].value_counts().to_dict()
    print(f"  Difficulty distribution: {dist}")

    out_fname = fname.replace("taxmap_", "diffclass_")
    df.to_csv(INTERIM_DIR / out_fname, index=False)
    print(f"  [+] Saved -> {out_fname}")

    return {
        "dataset": name,
        "Easy": dist.get("Easy", 0),
        "Medium": dist.get("Medium", 0),
        "Hard": dist.get("Hard", 0),
        "Novel": dist.get("Novel", 0),
        "total": len(df),
    }


def main():
    print(f"\n{'#'*60}")
    print(f"  PHASE 8 -- DIFFICULTY CLASSIFICATION")
    print(f"{'#'*60}")

    report_rows = []
    for name, fname in DATASET_CONFIG:
        banner(f"Classifying {name}")
        row = process_dataset(name, fname)
        if row:
            report_rows.append(row)

    report_df = pd.DataFrame(report_rows)
    report_path = REPORTS_DIR / "difficulty_report.csv"
    report_df.to_csv(report_path, index=False)
    print(f"\n  [+] Difficulty report saved -> {report_path}")

    print("\n  Overall difficulty distribution:")
    for diff in ["Easy", "Medium", "Hard", "Novel"]:
        total = report_df[diff].sum() if diff in report_df.columns else 0
        print(f"    {diff:<10}: {total}")

    print(f"\n{'#'*60}")
    print(f"  PHASE 8 COMPLETE [OK]")
    print(f"{'#'*60}\n")


if __name__ == "__main__":
    main()
