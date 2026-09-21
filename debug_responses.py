import pandas as pd

df = pd.read_csv('reports/assessment_results_tfidf_lr_medium.csv')
for i, r in df.iterrows():
    print(f"--- Row {i} | attack_type={r['attack_type']} | refusal={r['refusal_detected']} | attack_ok={r['attack_successful']}")
    print(f"RESP: {str(r['target_response'])[:400]}")
    print()
