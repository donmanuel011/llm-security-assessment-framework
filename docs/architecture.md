# System Architecture

## Overview
The **LLM Security Assessment Framework** is an end-to-end security auditing and prompt defense platform.

```
                    ┌─────────────────────────┐
                    │ Raw Attack Datasets     │
                    │ (HarmBench, PIBench,    │
                    │  TensorTrust, JB-Bench) │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ Data Processing Pipeline│
                    │ (Norm, Clean, Dedup,    │
                    │  Taxonomy Mapping)      │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ Leakage-Aware Splitting │
                    │ (Train/Val/Known/Novel) │
                    └────────────┬────────────┘
                                 │
        ┌────────────────────────┴────────────────────────┐
        ▼                                                 ▼
┌──────────────────────────┐                    ┌──────────────────────────┐
│ Detection Subsystem      │                    │ Assessment Subsystem     │
│ (TF-IDF LR/SVM,          │                    │ (Mock / Local / API      │
│  DistilBERT, DeBERTa-v3) │                    │  Target Model Adapters)  │
└───────────┬──────────────┘                    └────────────┬─────────────┘
            │                                                │
            └────────────────────────┬───────────────────────┘
                                     ▼
                        ┌──────────────────────────┐
                        │ Risk Scoring Engine      │
                        │ & Streamlit Dashboard    │
                        └──────────────────────────┘
```

## Core Modules
1. **Data Processing (`src/data_processing/`)**: Normalization, deduplication, taxonomy mapping, difficulty classification, variant generation.
2. **Detection Subsystem (`src/detection/`)**: Scikit-learn and Transformer classifiers for binary (Benign vs Malicious) and multi-class security labels.
3. **Target Model Adapter (`src/assessment/model_adapter.py`)**: Abstract interface supporting offline mock models, local HuggingFace LLMs, and API endpoints.
4. **Response Evaluator (`src/assessment/response_evaluator.py`)**: Rule-based and heuristic refusal detection scoring.
5. **Risk Scoring Engine (`src/assessment/risk_scoring.py`)**: Dynamic risk formula combining attack severity, evasion status, and target LLM refusal posture.
