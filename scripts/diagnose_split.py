import pandas as pd, numpy as np, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
df = pd.read_csv(ROOT / "data/processed/split_dataset.csv")
df["prompt"] = df["prompt"].fillna("").astype(str)

print(f"Total rows: {len(df)}")
print(f"Null prompts: {df['prompt'].isna().sum()}")
print(f"Empty prompts: {(df['prompt'].str.strip() == '').sum()}")
print()

for split in ["train", "val", "test_known", "test_novel"]:
    s = df[df["split"] == split]
    mal = (s["label"] == "malicious").sum()
    ben = (s["label"] == "benign").sum()
    ratio = mal / len(s) * 100 if len(s) > 0 else 0
    print(f"=== {split} ({len(s)} rows) ===")
    print(f"  malicious: {mal}  benign: {ben}  ({ratio:.1f}% malicious)")
    print(s["unified_label"].value_counts().to_string())
    print()

print("Binary label NaN check:", df["label"].isna().sum())
print("Unique labels:", df["label"].unique())
print("Unique unified_labels:", df["unified_label"].unique())
