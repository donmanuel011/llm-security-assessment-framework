"""
Attack Runner (Phase 18).
Loads attacks from assessment dataset or unified dataset and prepares them for testing pipeline.
"""

import sys
import pathlib
import pandas as pd

SCRIPT_DIR   = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.detection.model_config import PROCESSED_DIR

def load_attack_dataset(sample_size: int = None):
    """
    Loads assessment attacks dataset.
    """
    assess_path = PROCESSED_DIR / "assessment_dataset.csv"
    if not assess_path.exists():
        assess_path = PROCESSED_DIR / "unified_dataset.csv"

    df = pd.read_csv(assess_path)
    df["prompt"] = df["prompt"].fillna("")

    if sample_size and sample_size < len(df):
        df = df.sample(n=sample_size, random_state=42).reset_index(drop=True)

    return df
