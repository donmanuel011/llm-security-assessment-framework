# LLM Security Assessment Framework: AI-Based Prompt Injection and Jailbreak Detection

## 1. Project Title
LLM Security Assessment Framework: AI-Based Prompt Injection and Jailbreak Detection

## 2. Project Overview
Large Language Models (LLMs) are increasingly integrated into critical applications, making their security a paramount concern. This project develops an AI-driven security assessment framework designed to evaluate the robustness and safety of LLM applications against adversarial inputs, specifically prompt injection, jailbreaking, indirect prompt injection, and prompt leakage attacks. The framework aims to provide a comprehensive suite for dataset preparation, AI-based prompt detection, and automated security evaluation of LLM applications.

## 3. Problem Statement
As LLM adoption grows, so does the risk of adversarial attacks designed to bypass safety guardrails, leak sensitive information, or hijack the model's intended behavior. Current assessment methodologies often lack comprehensive, standardized datasets and automated detection mechanisms capable of adapting to novel attack vectors. There is a critical need for a robust framework that can systematically evaluate LLM vulnerabilities and detect malicious prompts before they reach the model.

## 4. Objectives
*   **Adversarial Dataset Curation:** Create a comprehensive and balanced dataset by integrating established benchmarks (HarmBench, PIBench) with benign prompts.
*   **AI-Based Attack Detection:** Develop and evaluate a robust prompt detector using transformer models (e.g., DeBERTa) to classify inputs based on a defined attack taxonomy.
*   **Automated LLM Assessment:** Implement a pipeline to systematically test LLM applications with adversarial prompts and evaluate their responses.
*   **Robustness Evaluation:** Assess the generalization capability of the framework against known, modified, and potentially unseen attack patterns.
*   **Actionable Reporting:** Generate automated security reports with key metrics and risk scoring to quantify identified vulnerabilities.

## 5. Key Features
*   **Unified Dataset Processing Pipeline:** Automated cleaning, normalization, deduplication, and taxonomy-based labeling of diverse prompt sources.
*   **Transformer-Based Detection Model:** Fine-tuned DeBERTa model for high-accuracy prompt classification.
*   **Automated Security Evaluation:** End-to-end testing of LLM targets with detailed response evaluation (success/refusal).
*   **Comprehensive Metrics & Risk Assessment:** Calculation of standard classification metrics and customized risk scores for identified vulnerabilities.
*   **Interactive Dashboard:** Streamlit-based interface for visualizing security assessments and generating reports.

## 6. Attack Taxonomy
The framework categorizes prompts into the following taxonomy to facilitate granular detection and assessment:
*   **Benign Prompt:** Standard, non-malicious user queries.
*   **Prompt Injection (PI):** Malicious inputs designed to override the original instructions of the LLM application.
*   **Jailbreak:** Techniques aimed at bypassing the LLM's built-in safety guardrails and ethical constraints.
*   **Indirect Prompt Injection:** Attacks where the malicious instructions are embedded in external data (e.g., websites, documents) retrieved by the LLM.
*   **Prompt Leakage:** Attempts to extract the system prompt or internal instructions of the LLM application.

## 7. System Architecture

```text
+---------------------------------------------------+
|               Data Sources                        |
|  [HarmBench] + [PIBench] + [Benign Dataset]       |
+---------------------------------------------------+
                         |
                         v
+---------------------------------------------------+
|             Dataset Processing                    |
| - Cleaning & Normalization                        |
| - Deduplication                                   |
| - Attack Taxonomy & Labeling                      |
+---------------------------------------------------+
                         |
                         v
+---------------------------------------------------+
|               Unified Dataset                     |
+---------------------------------------------------+
            |                          |
            v                          v
+------------------------+  +-----------------------+
|  Detector Training &   |  |   Automated LLM       |
|  Evaluation            |  |   Assessment          |
|  (DeBERTa Model)       |  |   (Adversarial Test)  |
+------------------------+  +-----------------------+
            |                          |
            v                          v
+---------------------------------------------------+
|               Response Evaluation                 |
|       (Attack Success vs. Model Refusal)          |
+---------------------------------------------------+
                         |
                         v
+---------------------------------------------------+
|       Security Metrics & Risk Assessment          |
| - Accuracy, Precision, Recall, F1-Score           |
| - Attack Success Rate, Refusal Rate               |
| - Vulnerability Risk Scoring                      |
+---------------------------------------------------+
                         |
                         v
+---------------------------------------------------+
|         Dashboard / Security Report               |
|             (Streamlit Web App)                   |
+---------------------------------------------------+
```

## 8. Dataset
The framework utilizes a structured approach to data management, separating training data for the detector from assessment data for LLM evaluation.

### Structure
*   **`detector_dataset.csv`**: Used for training, validation, and testing the AI-based prompt detector.
*   **`assessment_dataset.csv`**: Used for the automated security evaluation of target LLM applications.

### Metadata Schema
Both datasets incorporate the following metadata fields where applicable:
`Sample ID`, `Prompt Text`, `Label` (Benign/Malicious), `Attack Type` (Taxonomy), `Subtype`, `Source` (e.g., HarmBench), `Difficulty/Severity`, `Language`, `Target Model`, `Model Response`, `Detector Prediction`, `Detector Confidence`, `Attack Success (Boolean)`, `Refusal (Boolean)`, `Risk Score`, `Evaluation Method`.

## 9. Methodology
1.  **Data Ingestion & Integration:** Aggregate adversarial datasets (HarmBench, PIBench) and benign conversational datasets.
2.  **Preprocessing & Labeling:** Cleanse the text data, remove duplicates, and map each prompt to the defined Attack Taxonomy.
3.  **Detector Development:** Fine-tune a DeBERTa sequence classification model on `detector_dataset.csv` to distinguish between benign and various malicious prompt categories.
4.  **Assessment Pipeline:** Feed prompts from `assessment_dataset.csv` into target LLM applications.
5.  **Response Analysis:** Evaluate the LLM's output to determine if the attack was successful (e.g., the model complied with a jailbreak) or if the model safely refused the prompt.
6.  **Reporting:** Calculate aggregate security metrics and generate comprehensive reports.

## 10. Machine Learning Model
*   **Architecture:** [DeBERTa](https://huggingface.co/docs/transformers/model_doc/deberta) (Decoding-enhanced BERT with disentangled attention).
*   **Task:** Sequence Classification (Multi-class classification based on the Attack Taxonomy).
*   **Rationale:** DeBERTa offers superior performance in natural language understanding tasks compared to standard BERT models, making it well-suited for capturing the subtle linguistic nuances often present in sophisticated prompt injections and jailbreaks.

## 11. Evaluation Metrics
The framework evaluates both the prompt detector and the target LLM application.

**Prompt Detector Metrics:**
*   Accuracy
*   Precision
*   Recall
*   F1-Score

**LLM Security Assessment Metrics:**
*   **Attack Success Rate (ASR):** The percentage of malicious prompts that successfully bypassed the model's defenses.
*   **Refusal Rate:** The percentage of malicious prompts that the model correctly identified and refused to answer.
*   **Risk Score:** A composite score calculating the overall vulnerability of the LLM based on ASR, severity of successful attacks, and exposure.

## 12. Project Structure
```text
llm-security-assessment-framework/
├── data/
│   ├── raw/                 # Raw datasets (HarmBench, PIBench, etc.)
│   ├── processed/           # detector_dataset.csv, assessment_dataset.csv
│   └── interim/             # Intermediate processing files
├── src/
│   ├── data_processing/     # Scripts for cleaning, deduplication, labeling
│   ├── models/              # DeBERTa model training and evaluation scripts
│   ├── assessment/          # Automated LLM testing and response evaluation
│   └── utils/               # Helper functions
├── notebooks/               # Jupyter notebooks for EDA and prototyping
├── app/                     # Streamlit dashboard application
├── reports/                 # Generated security reports and visualizations
├── requirements.txt         # Project dependencies
└── README.md                # Project documentation
```

## 13. Technology Stack
*   **Programming Language:** Python 3.9+
*   **Deep Learning Framework:** PyTorch
*   **NLP Library:** Hugging Face Transformers
*   **Core Model:** DeBERTa
*   **Data Manipulation:** Pandas, NumPy
*   **Machine Learning Utilities:** Scikit-learn
*   **Development & Prototyping:** Jupyter Notebook
*   **Web Dashboard:** Streamlit
*   **Version Control:** Git & GitHub

## 14. Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/llm-security-assessment-framework.git
    cd llm-security-assessment-framework
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## 15. Usage

The framework consists of a sequential execution pipeline divided into phases.

**Basic Pipeline Execution:**

1.  **Data Processing (Phases 1-12):**
    The data pipeline cleans, dedups, and assigns taxonomies to the datasets, then splits them for model training and assessment.
    ```bash
    python src/data_processing/phase12_split.py
    ```
2.  **Dataset Analysis (Phase 11):**
    Visualizations and metrics on the datasets are generated via the `notebooks/dataset_analysis.ipynb` and `reports/figures/`.
3.  **Train Baseline Detectors (Phase 13):**
    ```bash
    python src/models/baseline_models.py
    ```
4.  **Train Final DeBERTa Detector (Phase 14 - Upcoming):**
    ```bash
    # (Command to be implemented)
    ```
5.  **Run LLM Security Assessment (Upcoming):**
    ```bash
    # (Command to be implemented)
    ```
6.  **Launch Dashboard (Upcoming):**
    ```bash
    streamlit run app/main.py
    ```

## 16. Current Results

*   **Dataset Overview:**
    *   Unified dataset contains **1,984 samples**.
    *   Classes: Jailbreak (810), Prompt Injection (511), Prompt Leakage (408), Benign (232), Indirect Prompt Injection (23).
*   **Detector Performance (Baseline Binary Classification):**
    Evaluating benign vs. attack samples on test splits.

    | Model | Split | Accuracy | Precision | Recall | F1-Score |
    | :--- | :--- | :--- | :--- | :--- | :--- |
    | TF-IDF + Logistic Regression | Known Attacks | 95.1% | 94.9% | 100.0% | 97.4% |
    | TF-IDF + Logistic Regression | Novel Attacks | 88.0% | 87.5% | 100.0% | 93.3% |
    | TF-IDF + SVM | Known Attacks | 97.8% | 99.0% | 98.5% | 98.8% |
    | TF-IDF + SVM | Novel Attacks | 96.0% | 95.5% | 100.0% | 97.7% |
    | DistilBERT (Fine-tuned) | Known Attacks | 98.2% | 98.1% | 100.0% | 99.0% |
    | DistilBERT (Fine-tuned) | Novel Attacks | 91.0% | 90.3% | 100.0% | 94.9% |

*   **Assessment of Target LLM:**
    *   *(To be evaluated in later phases)*

## 17. Future Enhancements
*   Integration with more comprehensive vulnerability databases (e.g., MITRE ATLAS).
*   Development of a "Red Teaming" agent to dynamically generate novel adversarial prompts during the assessment phase.
*   Support for evaluating multimodal LLMs (vision-language models).
*   Real-time prompt filtering API for integration into production LLM applications.

## 18. Ethical and Security Considerations
This framework is developed strictly for defensive and academic research purposes. The adversarial datasets and assessment tools must only be used to evaluate and improve the security of LLM applications with appropriate authorization. Do not use this tool to attack or exploit systems without explicit permission.

## 19. References
*   [HarmBench: A Standardized Evaluation Framework for Automated Red Teaming and Robust Refusal](https://arxiv.org/abs/2402.04249)
*   [PIBench: Prompt Injection Benchmark](https://arxiv.org/abs/2405.02111)
*   [DeBERTa: Decoding-enhanced BERT with Disentangled Attention](https://arxiv.org/abs/2006.03654)
*   [OWASP Top 10 for Large Language Model Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
