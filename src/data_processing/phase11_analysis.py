"""
Phase 11 -- Dataset Analysis
==============================
Loads unified_dataset.csv and generates all required analysis charts.
All figures are saved to reports/figures/.
Also computes class imbalance metrics and duplicate rate.
"""

import sys
import io
import pathlib
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

# UTF-8 stdout
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR    = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT  = SCRIPT_DIR.parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR   = PROJECT_ROOT / "reports"
FIGURES_DIR   = REPORTS_DIR / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# ── Style ──────────────────────────────────────────────────────────────────────
PALETTE = [
    "#4C72B0", "#DD8452", "#55A868", "#C44E52",
    "#8172B2", "#937860", "#DA8BC3", "#8C8C8C",
]
sns.set_theme(style="whitegrid", palette=PALETTE)
plt.rcParams.update({
    "figure.dpi": 120,
    "figure.facecolor": "white",
    "axes.titlesize": 13,
    "axes.labelsize": 11,
})

def save_fig(name: str):
    path = FIGURES_DIR / name
    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  [+] Saved -> reports/figures/{name}")

def banner(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def plot_class_distribution(df: pd.DataFrame):
    banner("1. Class (Unified Label) Distribution")
    counts = df["unified_label"].value_counts()
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(counts.index, counts.values, color=PALETTE[:len(counts)], edgecolor="white")
    ax.bar_label(bars, labels=[f"{v:,}" for v in counts.values], padding=4, fontsize=10)
    ax.set_title("Unified Label (Class) Distribution")
    ax.set_xlabel("Class")
    ax.set_ylabel("Count")
    ax.set_xticklabels(counts.index, rotation=20, ha="right")
    save_fig("01_class_distribution.png")
    print(counts.to_string())


def plot_source_distribution(df: pd.DataFrame):
    banner("2. Source Distribution")
    counts = df["source"].value_counts()
    fig, ax = plt.subplots(figsize=(7, 5))
    wedges, texts, autotexts = ax.pie(
        counts.values, labels=counts.index,
        autopct="%1.1f%%", colors=PALETTE[:len(counts)],
        startangle=140, pctdistance=0.8
    )
    for t in autotexts:
        t.set_fontsize(9)
    ax.set_title("Source Dataset Distribution")
    save_fig("02_source_distribution.png")
    print(counts.to_string())


def plot_attack_type_distribution(df: pd.DataFrame):
    banner("3. Attack Type Distribution")
    # Exclude benign for attack-type chart
    malicious = df[df["label"] == "malicious"]
    counts = malicious["unified_label"].value_counts()
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.barh(counts.index, counts.values, color=PALETTE[:len(counts)], edgecolor="white")
    ax.bar_label(bars, labels=[f"{v:,}" for v in counts.values], padding=4, fontsize=10)
    ax.set_title("Attack Type Distribution (Malicious Samples)")
    ax.set_xlabel("Count")
    ax.invert_yaxis()
    save_fig("03_attack_type_distribution.png")
    print(counts.to_string())


def plot_difficulty_distribution(df: pd.DataFrame):
    banner("4. Difficulty Distribution")
    order = ["Easy", "Medium", "Hard", "Novel"]
    counts = df["difficulty"].value_counts().reindex(order).fillna(0).astype(int)
    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(counts.index, counts.values, color=PALETTE[:len(counts)], edgecolor="white")
    ax.bar_label(bars, labels=[f"{v:,}" for v in counts.values], padding=4, fontsize=10)
    ax.set_title("Difficulty Level Distribution")
    ax.set_xlabel("Difficulty")
    ax.set_ylabel("Count")
    save_fig("04_difficulty_distribution.png")
    print(counts.to_string())


def plot_prompt_length_distribution(df: pd.DataFrame):
    banner("5. Prompt Length Distribution")
    df2 = df.copy()
    df2["prompt_length"] = df2["prompt"].astype(str).str.len()
    # Cap at 1000 for readability
    df2["prompt_length_capped"] = df2["prompt_length"].clip(upper=1000)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # Histogram
    axes[0].hist(df2["prompt_length_capped"], bins=40, color=PALETTE[0], edgecolor="white")
    axes[0].set_title("Prompt Length Distribution (capped at 1000 chars)")
    axes[0].set_xlabel("Character Length")
    axes[0].set_ylabel("Frequency")

    # Boxplot by class
    melted = df2[["unified_label", "prompt_length"]].copy()
    melted["prompt_length"] = melted["prompt_length"].clip(upper=1500)
    labels = melted["unified_label"].unique()
    data_per_class = [melted[melted["unified_label"] == lbl]["prompt_length"].values for lbl in labels]
    axes[1].boxplot(data_per_class, labels=labels, patch_artist=True,
                    boxprops=dict(facecolor=PALETTE[1], color=PALETTE[0]),
                    medianprops=dict(color="white", linewidth=2))
    axes[1].set_title("Prompt Length by Class")
    axes[1].set_xlabel("Class")
    axes[1].set_ylabel("Character Length (capped at 1500)")
    axes[1].set_xticklabels(labels, rotation=20, ha="right")

    save_fig("05_prompt_length_distribution.png")
    print(f"  Mean length: {df2['prompt_length'].mean():.1f}  |  "
          f"Median: {df2['prompt_length'].median():.1f}  |  "
          f"Max: {df2['prompt_length'].max()}")


def plot_language_distribution(df: pd.DataFrame):
    banner("6. Language Distribution")
    counts = df["language"].value_counts()
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(counts.index.astype(str), counts.values, color=PALETTE[:len(counts)], edgecolor="white")
    ax.bar_label(bars, labels=[f"{v:,}" for v in counts.values], padding=4, fontsize=10)
    ax.set_title("Language Distribution")
    ax.set_xlabel("Language")
    ax.set_ylabel("Count")
    save_fig("06_language_distribution.png")
    print(counts.to_string())


def compute_duplicate_rate(df: pd.DataFrame):
    banner("7. Duplicate Rate")
    total = len(df)
    orig_only = df[df["transformation"] == "original"]
    exact_dups = orig_only.duplicated(subset=["prompt"], keep="first").sum()
    dup_rate = (exact_dups / total) * 100
    print(f"  Total rows          : {total:,}")
    print(f"  Exact duplicates    : {exact_dups:,}")
    print(f"  Duplicate rate      : {dup_rate:.2f}%")

    # Simple bar chart
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.bar(["Unique", "Duplicates"], [total - exact_dups, exact_dups],
           color=[PALETTE[2], PALETTE[3]], edgecolor="white")
    ax.set_title(f"Duplicate Rate ({dup_rate:.2f}%)")
    ax.set_ylabel("Count")
    for bar, val in zip(ax.patches, [total - exact_dups, exact_dups]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2,
                f"{val:,}", ha="center", va="bottom", fontsize=10)
    save_fig("07_duplicate_rate.png")


def compute_class_imbalance(df: pd.DataFrame):
    banner("8. Class Imbalance Metrics")
    counts = df["unified_label"].value_counts()
    total  = counts.sum()
    majority = counts.max()
    minority = counts.min()
    ir = majority / minority  # Imbalance Ratio

    print(f"  Total samples       : {total:,}")
    print(f"  Majority class      : {counts.idxmax()} ({majority:,})")
    print(f"  Minority class      : {counts.idxmin()} ({minority:,})")
    print(f"  Imbalance Ratio     : {ir:.2f}x")

    # Per-class proportions
    props = (counts / total * 100).round(2)
    print("\n  Class proportions:")
    for lbl, pct in props.items():
        print(f"    {str(lbl):<35}: {pct:.2f}%")

    # Chart
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(props.index, props.values, color=PALETTE[:len(props)], edgecolor="white")
    ax.bar_label(bars, labels=[f"{v:.1f}%" for v in props.values], padding=4, fontsize=10)
    ax.axhline(100 / len(counts), color="red", linestyle="--", linewidth=1.2,
               label=f"Ideal balance ({100/len(counts):.1f}%)")
    ax.set_title(f"Class Imbalance (IR = {ir:.1f}x)")
    ax.set_xlabel("Class")
    ax.set_ylabel("Proportion (%)")
    ax.set_xticklabels(props.index, rotation=20, ha="right")
    ax.legend()
    save_fig("08_class_imbalance.png")

    # Save imbalance metrics to CSV
    imb_df = pd.DataFrame({
        "unified_label": counts.index,
        "count": counts.values,
        "proportion_pct": props.values,
    })
    imb_path = REPORTS_DIR / "class_imbalance_metrics.csv"
    imb_df.to_csv(imb_path, index=False)
    print(f"\n  [+] Saved class imbalance metrics -> reports/class_imbalance_metrics.csv")


def plot_transformation_distribution(df: pd.DataFrame):
    banner("Bonus: Transformation Distribution")
    counts = df["transformation"].value_counts()
    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(counts.index, counts.values, color=PALETTE[:len(counts)], edgecolor="white")
    ax.bar_label(bars, labels=[f"{v:,}" for v in counts.values], padding=4, fontsize=10)
    ax.set_title("Transformation Type Distribution")
    ax.set_xlabel("Transformation")
    ax.set_ylabel("Count")
    ax.set_xticklabels(counts.index, rotation=15, ha="right")
    save_fig("09_transformation_distribution.png")
    print(counts.to_string())


def main():
    print(f"\n{'#'*60}")
    print(f"  PHASE 11 -- DATASET ANALYSIS")
    print(f"{'#'*60}")

    unified_path = PROCESSED_DIR / "unified_dataset.csv"
    if not unified_path.exists():
        print(f"  [ERROR] unified_dataset.csv not found at {unified_path}")
        return

    df = pd.read_csv(unified_path)
    df["prompt"]   = df["prompt"].fillna("")
    df["language"] = df["language"].fillna("en")
    print(f"\n  Loaded {len(df):,} rows from unified_dataset.csv")
    print(f"  Columns: {list(df.columns)}")

    plot_class_distribution(df)
    plot_source_distribution(df)
    plot_attack_type_distribution(df)
    plot_difficulty_distribution(df)
    plot_prompt_length_distribution(df)
    plot_language_distribution(df)
    compute_duplicate_rate(df)
    compute_class_imbalance(df)
    plot_transformation_distribution(df)

    print(f"\n  All figures saved to -> reports/figures/")
    print(f"\n{'#'*60}")
    print(f"  PHASE 11 COMPLETE [OK]")
    print(f"{'#'*60}\n")


if __name__ == "__main__":
    main()
