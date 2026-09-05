import os
import pandas as pd
import re

def clean_text(text):
    if pd.isna(text):
        return ""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', str(text))
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def process_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    RAW_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(current_dir)), "data", "raw")
    PROCESSED_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(current_dir)), "data", "processed")
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

    # 1. Load Data
    try:
        harmbench = pd.read_csv(os.path.join(RAW_DATA_DIR, "harmbench_raw.csv"))
        pibench = pd.read_csv(os.path.join(RAW_DATA_DIR, "pibench_raw.csv"))
        benign = pd.read_csv(os.path.join(RAW_DATA_DIR, "benign_raw.csv"))
    except FileNotFoundError as e:
        print(f"Error: Could not find raw datasets. Please run ingest_data.py first. {e}")
        return

    # 2. Schema Mapping & Taxonomy Labeling
    
    # Unified Schema: Prompt Text, Label, Source, Attack Type
    
    # Harmbench mapping
    df_harmbench = pd.DataFrame()
    df_harmbench['Prompt Text'] = harmbench['prompt'].apply(clean_text)
    df_harmbench['Label'] = 'Malicious'
    df_harmbench['Source'] = 'HarmBench'
    df_harmbench['Attack Type'] = 'Jailbreak'
    
    # PIBench mapping
    df_pibench = pd.DataFrame()
    df_pibench['Prompt Text'] = pibench['prompt'].apply(clean_text)
    df_pibench['Label'] = 'Malicious'
    df_pibench['Source'] = 'PIBench'
    
    def map_pibench_attack(attack):
        attack = str(attack).lower()
        if 'indirect' in attack:
            return 'Indirect PI'
        elif 'jailbreak' in attack:
            return 'Jailbreak'
        else:
            return 'Prompt Injection'
            
    df_pibench['Attack Type'] = pibench['attack_type'].apply(map_pibench_attack)
    
    # Benign mapping
    df_benign = pd.DataFrame()
    df_benign['Prompt Text'] = (benign['instruction'] + " " + benign['context'].fillna('')).apply(clean_text)
    df_benign['Label'] = 'Benign'
    df_benign['Source'] = 'Databricks Dolly'
    df_benign['Attack Type'] = 'Benign'
    
    # Combine datasets
    df_combined = pd.concat([df_harmbench, df_pibench, df_benign], ignore_index=True)
    
    # 3. Deduplication
    initial_len = len(df_combined)
    df_combined = df_combined.drop_duplicates(subset=['Prompt Text'], keep='first')
    df_combined = df_combined[df_combined['Prompt Text'] != ""] # Remove empty prompts
    final_len = len(df_combined)
    print(f"Deduplication removed {initial_len - final_len} overlapping or empty prompts.")
    
    # Save combined dataset
    output_path = os.path.join(PROCESSED_DATA_DIR, "unified_dataset.csv")
    df_combined.to_csv(output_path, index=False)
    print(f"Phase 3 Complete. Saved unified dataset to {output_path}")

if __name__ == "__main__":
    process_data()
