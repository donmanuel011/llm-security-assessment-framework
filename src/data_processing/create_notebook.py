import nbformat as nbf
import os
import pathlib

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)

nb = nbf.v4.new_notebook()

text = """\
# Phase 11 -- Dataset Analysis

This notebook analyzes the `unified_dataset.csv` assembled in Phase 10.
It visualizes class distributions, source breakdown, difficulty, and prompt lengths.
"""

code1 = """\
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Style
PALETTE = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B2", "#937860", "#DA8BC3", "#8C8C8C"]
sns.set_theme(style="whitegrid", palette=PALETTE)
plt.rcParams.update({"figure.figsize": (8, 5), "figure.dpi": 100})

# Load Data
processed_dir = Path("../data/processed")
df = pd.read_csv(processed_dir / "unified_dataset.csv")
df["prompt"] = df["prompt"].fillna("")
df["language"] = df["language"].fillna("en")

print(f"Loaded {len(df):,} rows.")
df.head(3)
"""

code2 = """\
# 1. Class Distribution
counts = df["unified_label"].value_counts()
ax = counts.plot.bar(color=PALETTE[:len(counts)], edgecolor="white")
ax.bar_label(ax.containers[0], padding=3)
plt.title("Unified Label (Class) Distribution")
plt.ylabel("Count")
plt.xticks(rotation=20, ha="right")
plt.show()
"""

code3 = """\
# 2. Source Distribution
counts = df["source"].value_counts()
plt.pie(counts, labels=counts.index, autopct="%1.1f%%", colors=PALETTE[:len(counts)], startangle=140)
plt.title("Source Dataset Distribution")
plt.show()
"""

code4 = """\
# 3. Attack Type Distribution
malicious = df[df["label"] == "malicious"]
counts = malicious["unified_label"].value_counts()
ax = counts.plot.barh(color=PALETTE[:len(counts)], edgecolor="white")
ax.bar_label(ax.containers[0], padding=3)
plt.title("Attack Type Distribution (Malicious Samples)")
plt.xlabel("Count")
plt.gca().invert_yaxis()
plt.show()
"""

code5 = """\
# 4. Difficulty Distribution
order = ["Easy", "Medium", "Hard", "Novel"]
counts = df["difficulty"].value_counts().reindex(order).fillna(0).astype(int)
ax = counts.plot.bar(color=PALETTE[:len(counts)], edgecolor="white")
ax.bar_label(ax.containers[0], padding=3)
plt.title("Difficulty Level Distribution")
plt.ylabel("Count")
plt.xticks(rotation=0)
plt.show()
"""

code6 = """\
# 5. Prompt Length Distribution
df2 = df.copy()
df2["prompt_length"] = df2["prompt"].astype(str).str.len()
df2["prompt_length_capped"] = df2["prompt_length"].clip(upper=1000)

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
axes[0].hist(df2["prompt_length_capped"], bins=40, color=PALETTE[0], edgecolor="white")
axes[0].set_title("Prompt Length Distribution (capped at 1000 chars)")

melted = df2[["unified_label", "prompt_length"]].copy()
melted["prompt_length"] = melted["prompt_length"].clip(upper=1500)
sns.boxplot(data=melted, x="unified_label", y="prompt_length", ax=axes[1], color=PALETTE[1])
axes[1].set_title("Prompt Length by Class")
axes[1].tick_params(axis="x", rotation=20)
plt.show()
"""

code7 = """\
# 6. Duplicate Rate
total = len(df)
orig_only = df[df["transformation"] == "original"]
exact_dups = orig_only.duplicated(subset=["prompt"], keep="first").sum()
dup_rate = (exact_dups / total) * 100
print(f"Total rows: {total:,}")
print(f"Exact duplicates: {exact_dups:,}")
print(f"Duplicate rate: {dup_rate:.2f}%")
"""

nb["cells"] = [
    nbf.v4.new_markdown_cell(text),
    nbf.v4.new_code_cell(code1),
    nbf.v4.new_code_cell(code2),
    nbf.v4.new_code_cell(code3),
    nbf.v4.new_code_cell(code4),
    nbf.v4.new_code_cell(code5),
    nbf.v4.new_code_cell(code6),
    nbf.v4.new_code_cell(code7)
]

path = NOTEBOOKS_DIR / "dataset_analysis.ipynb"
with open(path, "w", encoding="utf-8") as f:
    nbf.write(nb, f)
print(f"Created {path}")
