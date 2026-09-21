import sys, pathlib, pandas as pd
sys.path.insert(0, str(pathlib.Path('.').resolve()))
from src.assessment.model_adapter import GroqAdapter
from src.assessment.response_evaluator import evaluate_target_response
from src.detection.model_config import PROCESSED_DIR

df = pd.read_csv(PROCESSED_DIR / 'assessment_dataset.csv')
df['prompt'] = df['prompt'].fillna('')
sample = df.sample(n=6, random_state=42).reset_index(drop=True)
adapter = GroqAdapter()
print('='*80)
for i, row in sample.iterrows():
    prompt = str(row['prompt'])
    atype = str(row.get('unified_label', row.get('attack_type','?')))
    result = adapter.generate(prompt)
    response = result['response']
    ev = evaluate_target_response(prompt, response, is_attack_prompt=True)
    print(f'[{i+1}] {atype}')
    print(f'PROMPT  : {prompt[:180]}')
    print(f'RESPONSE: {response[:400]}')
    print(f'EVAL    : refusal={ev["refusal_detected"]} rule={ev["rule_based_refusal"]} heuristic={ev["heuristic_refusal"]} success={ev["attack_successful"]}')
    print('-'*80)
