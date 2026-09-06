# LLM Security Assessment Framework — Master Tasklist

> **Priority Tiers**
> 🔴 **MUST COMPLETE** — Core deliverables required for the final submission
> 🟡 **STRONGLY RECOMMENDED** — Significantly strengthen research quality
> 🟢 **FUTURE SCOPE** — Extensions beyond the core submission

---

## 🔴 MUST COMPLETE

---

### Phase 1 — Dataset Acquisition

#### 1.1 HarmBench
- [x] Download official HarmBench dataset → `data/raw/harmbench/`
- [x] Verify all downloaded files are intact
- [x] Record dataset version
- [x] Record source URL
- [x] Record total number of samples

#### 1.2 PIBench
- [x] Download PIBench dataset → `data/raw/pibench/`
- [x] Verify complete dataset download
- [x] Inspect data format (CSV / JSON / JSONL)
- [x] Record version and source URL
- [x] Identify injection vs. benign label columns

#### 1.3 Tensor Trust
- [x] Download Tensor Trust dataset → `data/raw/tensor_trust/`
- [x] Identify benchmark/raw files relevant to this project
- [x] Inspect schema (columns, types, values)
- [x] Determine which samples are suitable for training
- [x] Determine which samples should be reserved for evaluation

#### 1.4 JailbreakBench
- [x] Download JBB-Behaviors → `data/raw/jailbreakbench/`
- [x] Obtain harmful behaviors subset
- [x] Obtain benign behaviors subset
- [x] Obtain jailbreak artifacts where appropriate
- [x] Record dataset version

#### 1.5 Benign Dataset
- [x] Source standard user queries (e.g., Dolly, Alpaca, OpenAssistant)
- [x] Source general user queries
- [x] Source coding queries
- [x] Source educational queries
- [x] Source technical queries
- [x] Source security-related **legitimate** queries
- [x] Source RAG-related **legitimate** queries
- [x] Verify diversity — benign prompts must not look suspicious

---

### Phase 2 — Dataset Inspection

- [x] Create `src/data_processing/inspect_harmbench.py`
- [x] Create `src/data_processing/inspect_pibench.py`
- [x] Create `src/data_processing/inspect_tensor_trust.py`
- [x] Create `src/data_processing/inspect_jailbreakbench.py`

For each dataset, record:
- [x] Number of samples
- [x] Columns and data types
- [x] Label values and distribution
- [x] Attack categories present
- [x] Missing value counts
- [x] Duplicate sample counts
- [x] Average and distribution of prompt length
- [x] Language(s) present
- [x] Source metadata fields

- [x] Generate `reports/dataset_inventory.csv` summarizing all of the above

---

### Phase 3 — Dataset Normalization

Define common schema:
`sample_id`, `prompt`, `label`, `attack_type`, `attack_subtype`, `source`, `language`, `difficulty`, `prompt_length`, `attack_objective`, `obfuscation`, `transformation`, `context_dependency`, `severity`

- [x] Normalize HarmBench → common schema
- [x] Normalize PIBench → common schema
- [x] Normalize Tensor Trust → common schema
- [x] Normalize JailbreakBench → common schema
- [x] Normalize Benign dataset → common schema

---

### Phase 4 — Data Cleaning

#### 4.1 Missing Value Handling
- [x] Detect and handle NULL prompts
- [x] Detect and handle empty/whitespace-only prompts
- [x] Detect and handle invalid or missing labels
- [ ] Detect and handle missing attack category fields

#### 4.2 Text Normalization
- [x] Apply Unicode normalization
- [x] Normalize whitespace
- [x] Fix encoding problems / malformed records
- [ ] Verify adversarial characteristics are preserved:
  - [ ] Unusual capitalization retained
  - [ ] Special characters retained
  - [ ] Deliberate spacing retained
  - [ ] Encoding/obfuscation retained

---

### Phase 5 — Deduplication (Within-Dataset)

- [x] Implement exact duplicate detection via SHA-256(prompt)
- [ ] Implement near-duplicate detection using TF-IDF + cosine similarity
- [ ] Implement near-duplicate detection using sentence embeddings
- [ ] Detect paraphrased variants of the same attack
- [ ] Detect near-identical reformulations
- [ ] Log and export deduplication report

---

### Phase 6 — Cross-Dataset Deduplication

- [ ] HarmBench ↔ PIBench deduplication
- [ ] HarmBench ↔ Tensor Trust deduplication
- [ ] HarmBench ↔ JailbreakBench deduplication
- [ ] PIBench ↔ Tensor Trust deduplication
- [ ] PIBench ↔ JailbreakBench deduplication
- [ ] Tensor Trust ↔ JailbreakBench deduplication
- [ ] Log cross-dataset overlap statistics

---

### Phase 7 — Taxonomy Mapping

- [ ] Create `src/data_processing/taxonomy_mapper.py`
- [ ] Define unified taxonomy categories:
  - Benign
  - Prompt Injection
  - Indirect Prompt Injection
  - Jailbreak
  - Prompt Leakage
- [ ] Map HarmBench categories → unified taxonomy
- [ ] Map PIBench categories → unified taxonomy
- [ ] Map Tensor Trust categories → unified taxonomy
- [ ] Map JailbreakBench categories → unified taxonomy

---

### Phase 8 — Difficulty Classification

Assign difficulty (`Easy` / `Medium` / `Hard` / `Novel`) based on:
- [ ] Obfuscation level
- [ ] Structural complexity
- [ ] Multi-step instruction chaining
- [ ] Context dependency
- [ ] Indirect delivery method
- [ ] Multi-turn nature
- [ ] Semantic subtlety

---

### Phase 9 — Attack Transformation

For selected attacks, create controlled variants:
- [ ] Original (baseline)
- [ ] Paraphrased
- [ ] Obfuscated
- [ ] Role-based framing
- [ ] Contextual embedding
- [ ] Multi-turn variant

- [ ] Record `transformation` field (do **not** overwrite original)

---

### Phase 10 — Unified Dataset

- [ ] Generate `data/processed/unified_dataset.csv` (master dataset)
- [ ] Generate `data/processed/detector_dataset.csv`
- [ ] Generate `data/processed/assessment_dataset.csv`

---

### Phase 11 — Dataset Analysis

- [ ] Create `notebooks/dataset_analysis.ipynb`
- [ ] Analyze and visualize:
  - [ ] Class distribution (Benign / Prompt Injection / Jailbreak / Indirect Injection / Prompt Leakage)
  - [ ] Source distribution (HarmBench / PIBench / Tensor Trust / JailbreakBench / Custom)
  - [ ] Attack type distribution
  - [ ] Difficulty distribution
  - [ ] Prompt length distribution
  - [ ] Language distribution
  - [ ] Duplicate rate
  - [ ] Class imbalance metrics
- [ ] Export graphs for final report

---

### Phase 12 — Train/Test Split Strategy

Leakage-aware split (do **not** use naive `train_test_split`):
- [ ] Implement stratified split:
  - 70% Training
  - 15% Validation
  - 10% Known Attack Test
  - 5% Novel/Unseen Attack Test
- [ ] Ensure near-duplicate variants are **not** split across train and test sets
- [ ] Verify no label leakage between splits

---

### Phase 13 — Baseline Models

- [ ] **Baseline 1** — TF-IDF + Logistic Regression
- [ ] **Baseline 2** — TF-IDF + SVM
- [ ] **Baseline 3** — BERT fine-tuned classifier
- [ ] Evaluate all baselines on the test set
- [ ] Record performance metrics for comparison table

---

### Phase 14 — DeBERTa Detector

Pipeline: `Prompt → Tokenizer → DeBERTa → Classification Layer → Prediction`

- [ ] Set up DeBERTa tokenizer and model (`microsoft/deberta-v3-base`)
- [ ] Train binary classifier: Benign vs. Attack
- [ ] Experiment with multi-class classifier:
  - Benign / Prompt Injection / Jailbreak / Indirect Injection / Prompt Leakage
- [ ] Save trained models to `models/deberta/`

---

### Phase 15 — Model Training

Create training infrastructure:
- [ ] `src/detection/train.py`
- [ ] `src/detection/predict.py`
- [ ] `src/detection/evaluate.py`
- [ ] `src/detection/model_config.py`

- [ ] Train all baseline models
- [ ] Train DeBERTa binary classifier
- [ ] Train DeBERTa multi-class classifier
- [ ] Save all models under `models/`

---

### Phase 16 — Detector Evaluation

Calculate for all models:
- [ ] Accuracy
- [ ] Precision, Recall, F1-score (per class)
- [ ] Macro F1, Weighted F1
- [ ] ROC-AUC (where applicable)
- [ ] Confusion matrix
- [ ] False Positive Rate (FPR)
- [ ] False Negative Rate (FNR) ← especially critical for security

---

### Phase 17 — Unseen Attack Evaluation

- [ ] Evaluate model on known attacks test set
- [ ] Evaluate model on modified/transformed attacks
- [ ] Evaluate model on unseen transformations
- [ ] Evaluate model on novel combinations
- [ ] Compare Known-Test F1 vs. Unseen-Test F1
- [ ] Analyze generalization gap

---

### Phase 18 — Target LLM Testing Engine

Create assessment subsystem:
- [ ] `src/assessment/attack_runner.py`
- [ ] `src/assessment/model_adapter.py`
- [ ] `src/assessment/response_evaluator.py`
- [ ] `src/assessment/assessment_engine.py`

Engine pipeline:
`Load Attack → Run Detector → Send to Target LLM → Capture Response → Evaluate Response → Store Result`

---

### Phase 19 — Target Model Adapter

- [ ] Design common `generate(prompt) → response` interface
- [ ] Implement adapter for at least one local model (e.g., Llama / Mistral / Gemma)
- [ ] Implement adapter for at least one API-based model (e.g., OpenAI / Gemini)
- [ ] Verify adapter abstraction allows easy extension

---

### Phase 20 — Response Evaluation

- [ ] Implement **Method 1** — Rule-based refusal detection (keyword matching)
- [ ] Implement **Method 2** — Classifier or LLM-judge refusal detection
- [ ] Compare accuracy of both methods
- [ ] Output: `attack_successful` (YES/NO), `refusal_detected` (YES/NO)

---

### Phase 21 — Attack Success Rate (ASR)

Calculate ASR = (Successful Attacks / Total Attacks) × 100, broken down by:
- [ ] Attack type
- [ ] Attack subtype
- [ ] Source dataset
- [ ] Difficulty level
- [ ] Transformation applied
- [ ] Target model

---

### Phase 22 — Risk Scoring

- [ ] Design risk scoring formula combining:
  - Attack severity
  - Detector confidence
  - Attack success
  - Potential impact
- [ ] Assign risk tier: `LOW` / `MEDIUM` / `HIGH` / `CRITICAL`
- [ ] Document formula in methodology
- [ ] Validate scoring on test set

---

### Phase 23 — Security Dashboard

Build Streamlit application `app/dashboard.py` with pages:
- [ ] Dashboard (overview / summary metrics)
- [ ] Dataset Explorer
- [ ] Attack Detection
- [ ] LLM Assessment
- [ ] Model Comparison
- [ ] Metrics
- [ ] Risk Analysis
- [ ] Reports

---

### Phase 24 — Visualizations

Include in dashboard and report:
- [ ] Confusion matrix
- [ ] Class distribution chart
- [ ] Attack type distribution chart
- [ ] ASR by attack type
- [ ] Refusal rate chart
- [ ] Model comparison table/chart
- [ ] Risk distribution chart
- [ ] Detection confidence histogram
- [ ] Known vs. unseen attack performance comparison

---

### Phase 25 — Automated Report Generation

- [ ] Generate `reports/assessment_report.pdf`
- [ ] Generate `reports/results.csv`
- [ ] Generate `reports/results.json`

Report must include:
- [ ] Target model details
- [ ] Number of tests run
- [ ] Detector performance summary
- [ ] Attack Success Rate breakdown
- [ ] Refusal rate
- [ ] Attack categories tested
- [ ] Highest-risk vulnerabilities identified
- [ ] Recommendations

---

### Phase 38 — Final Experiments

- [ ] **Experiment 1** — Baseline vs. DeBERTa comparison
- [ ] **Experiment 2** — Binary vs. multi-class classification
- [ ] **Experiment 3** — Known vs. unseen attack generalization
- [ ] **Experiment 4** — Per-attack-type performance breakdown
- [ ] **Experiment 5** — Different target LLMs
- [ ] **Experiment 6** — Different attack transformations
- [ ] **Experiment 7** — Response evaluator comparison (rule-based vs. LLM judge)

---

### Phase 39 — Documentation

- [ ] Update `README.md` with:
  - [ ] Project overview
  - [ ] Architecture diagram
  - [ ] Installation instructions
  - [ ] Dataset preparation guide
  - [ ] Training instructions
  - [ ] Testing instructions
  - [ ] Dashboard usage
  - [ ] Metrics reference
  - [ ] Results summary
  - [ ] Limitations
  - [ ] Future scope

- [ ] Create `docs/architecture.md`
- [ ] Create `docs/dataset.md`
- [ ] Create `docs/methodology.md`
- [ ] Create `docs/attack_taxonomy.md`
- [ ] Create `docs/model.md`
- [ ] Create `docs/evaluation.md`
- [ ] Create `docs/limitations.md`

---

### Phase 40 — Final Report

- [ ] Chapter 1 — Introduction (Background, Problem, Motivation, Objectives, Scope)
- [ ] Chapter 2 — Literature Review (Prompt Injection, Jailbreaking, LLM Security, Existing Frameworks & Datasets)
- [ ] Chapter 3 — Proposed Methodology (Architecture, Dataset Pipeline, Taxonomy, DeBERTa, Assessment Engine, Risk Scoring)
- [ ] Chapter 4 — Implementation (Technologies, Dataset Processing, Model Training, Assessment Engine, Dashboard)
- [ ] Chapter 5 — Results (Dataset Statistics, Model Performance, Confusion Matrix, ASR, Refusal Rate, Unseen Attack Performance, Model Comparison)
- [ ] Chapter 6 — Discussion (Findings, Strengths, Weaknesses, Limitations)
- [ ] Chapter 7 — Conclusion & Future Scope

---

## 🟡 STRONGLY RECOMMENDED

---

### Phase 26 — Explainability

- [ ] Integrate attention visualization for DeBERTa predictions
- [ ] Implement SHAP for token-level importance
- [ ] Implement LIME explanations
- [ ] Display top contributing tokens per prediction
- [ ] Add explainability view to dashboard
- [ ] Document as model attributions (not causal proof)

---

### Phase 27 — Real-Time Protection Gateway

Pipeline: `User Prompt → Security Gateway → DeBERTa → [Safe → LLM | Attack → Block/Flag]`

- [ ] Build `Security Gateway` middleware
- [ ] Implement `Monitor` mode
- [ ] Implement `Warn` mode
- [ ] Implement `Block` mode
- [ ] Implement `Quarantine` mode

---

### Phase 33 — Multi-LLM Benchmarking

- [ ] Select ≥3 target LLMs (e.g., Llama, Mistral, Gemma + API model)
- [ ] Run identical test suite against all models
- [ ] Generate comparative table: Model | Detection | ASR | Refusal Rate | Risk
- [ ] Analyze cross-model vulnerability patterns

---

### Phase 35 — Software Testing

- [ ] `tests/test_data_processing.py` — dataset loading & label mapping
- [ ] `tests/test_taxonomy.py` — taxonomy mapping correctness
- [ ] `tests/test_detector.py` — model inference correctness
- [ ] `tests/test_assessment.py` — API/model adapter tests
- [ ] `tests/test_response_evaluator.py` — refusal detection logic
- [ ] `tests/test_risk.py` — risk scoring formula validation

---

### Phase 36 — Security Testing of the Framework Itself

- [ ] Test with malformed/truncated prompts
- [ ] Test with extremely long prompts
- [ ] Test with Unicode attack inputs
- [ ] Test with encoded/obfuscated input
- [ ] Test with missing required fields
- [ ] Test with invalid model responses
- [ ] Test API failure / timeout handling
- [ ] Test rate limit and resource exhaustion scenarios

---

### Phase 37 — Performance Testing

- [ ] Measure inference latency (per prompt)
- [ ] Measure throughput (prompts/second)
- [ ] Measure memory consumption
- [ ] Measure CPU and GPU usage
- [ ] Measure dataset processing time
- [ ] Compare BERT vs. DeBERTa performance profile

---

## 🟢 FUTURE SCOPE

---

### Phase 28 — RAG Security

- [ ] Extend framework to cover RAG pipeline: `User → RAG App → Retriever → Documents → LLM`
- [ ] Test malicious document injection
- [ ] Test poisoned retrieval content
- [ ] Test indirect instructions in retrieved context
- [ ] Test context manipulation attacks

---

### Phase 29 — Agentic AI Security

- [ ] Test agents interacting with websites, APIs, files, databases, and external tools
- [ ] Evaluate: `Prompt Injection → Agent → Tool Invocation → Unauthorized Action?`
- [ ] Document agentic-specific attack surface

---

### Phase 30 — Multimodal Security

- [ ] Extend detector to accept image input (via OCR / Vision model)
- [ ] Extend detector to accept PDF input
- [ ] Extend detector to accept audio input (via ASR)
- [ ] Pipeline: `Modality → Extraction → Text → Security Detector`

---

### Phase 31 — Continuous Learning

- [ ] Build feedback loop: `New Attack → Assessment → Detection Failure → Human Validation → Dataset Update → Retraining → New Model`
- [ ] Implement dataset versioning
- [ ] Implement model versioning

---

### Phase 32 — Automated Attack Generation (Red-Teaming)

- [ ] Implement attack generator to produce variants from base attacks
- [ ] Run variants through detector + target LLM
- [ ] Collect successful attacks into evaluation dataset
- [ ] Document coverage limitations clearly

---

### Phase 34 — Enterprise Integration

- [ ] Design REST API for detection + assessment engine
- [ ] Design SIEM integration interface
- [ ] Design SOC monitoring hooks
- [ ] Design CI/CD security gate integration
- [ ] Document AI gateway compatibility

---

*Last updated: 2026-09-06*
