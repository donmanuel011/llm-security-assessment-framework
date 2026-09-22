import pandas as pd
from src.assessment.preflight_scanner import PreflightScanner

df = pd.read_csv('data/processed/assessment_dataset.csv')
preflight = PreflightScanner()

print('Testing Preflight Scanner against the dataset...')
flagged_count = 0
for idx, row in df.iterrows():
    res = preflight.scan(str(row['prompt']))
    if res['flagged']:
        flagged_count += 1
        if flagged_count <= 20:
            print(f"[FLAGGED] Reason: {res['reason']:<30} | Prompt: {str(row['prompt'])[:60]}...")

print(f'\nTotal flagged by Preflight Scanner: {flagged_count} / {len(df)}')
