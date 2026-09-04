# Tasklist for First 50% of the Project

This tasklist outlines the steps required to complete the first half of your **LLM Security Assessment Framework** project. The first 50% primarily focuses on establishing the project architecture, acquiring the data, standardizing it, and preparing the final datasets required for the AI model and the assessment pipeline.

## Phase 1: Project Setup & Infrastructure (0% - 10%)
The goal of this phase is to set up a robust development environment and project scaffolding.

- [x] **Initialize Version Control:** Initialize a local Git repository and connect it to GitHub.
- [x] **Environment Setup:** Create a Python virtual environment (e.g., `python -m venv venv`).
- [x] **Dependency Management:** Create a `requirements.txt` file including `pandas`, `numpy`, `torch`, `transformers`, `scikit-learn`, `jupyter`, and `streamlit`.
- [x] **Directory Structure:** Create the folder hierarchy outlined in the README (`data/raw/`, `data/processed/`, `src/data_processing/`, `notebooks/`, etc.).

## Phase 2: Data Acquisition & Ingestion (10% - 25%)
This phase involves gathering the raw materials (datasets) required for the framework.

- [x] **HarmBench Integration:** Locate, download, and store the raw HarmBench dataset into `data/raw/`.
- [x] **PIBench Integration:** Locate, download, and store the raw PIBench dataset into `data/raw/`.
- [x] **Benign Dataset Sourcing:** Identify and download a suitable dataset of standard, safe user queries (e.g., subsets of Databricks Dolly, Alpaca, or OpenAssistant) into `data/raw/`.
- [x] **Ingestion Scripts:** Write initial Python scripts/notebooks to load these disparate raw data formats (JSON, CSV, JSONL) into pandas DataFrames for inspection.

## Phase 3: Data Processing & Standardization (25% - 40%)
This is a critical phase where messy raw data is converted into a structured, unified format.

- [ ] **Data Cleaning:** Write functions in `src/data_processing/` to handle missing values, remove HTML tags, and normalize text encodings.
- [ ] **Schema Mapping:** Map the disparate columns from the three datasets to your unified **Metadata Schema** (`Prompt Text`, `Label`, `Source`, `Attack Type`, etc.).
- [ ] **Taxonomy Labeling:** Implement logic to classify and label prompts strictly according to your Attack Taxonomy (Benign, Prompt Injection, Jailbreak, Indirect PI, Prompt Leakage).
- [ ] **Deduplication:** Implement rigorous exact-match and semantic (optional) deduplication to ensure there are no overlapping prompts, especially between training and assessment sets.

## Phase 4: Dataset Generation & Validation (40% - 50%)
The final phase of the first half results in the actual datasets that will power the rest of the project.

- [ ] **Data Splitting Strategy:** Implement a script (e.g., `src/data_processing/build_datasets.py`) to perform a stratified split of the unified data. Ensure an equal/fair representation of all attack types in both sets.
- [ ] **Export Datasets:** Generate and save `detector_dataset.csv` (for DeBERTa) and `assessment_dataset.csv` (for the automated LLM assessment) into `data/processed/`.
- [ ] **Exploratory Data Analysis (EDA):** Create a Jupyter Notebook (`notebooks/01_eda_dataset.ipynb`) to visualize the processed data:
    - [ ] Plot the distribution of labels (Benign vs. Malicious).
    - [ ] Plot the distribution of attack subtypes.
    - [ ] Analyze the text length (token count) distribution to help inform DeBERTa max sequence length later.

---
**Note:** Once these tasks are completed, you will have reached the 50% milestone. You will have a clean, balanced, and structurally sound dataset ready to be fed into the DeBERTa model for training (Phase 5) and the LLM API for security assessment (Phase 6).
