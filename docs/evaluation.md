# Evaluation Metrics & Performance Benchmarks

## Benchmark Comparison Table

| Model | Split | Accuracy | Precision | Recall | F1 Score |
|---|---|---|---|---|---|
| TF-IDF + LR | Known Test | 95.07% | 94.88% | 100.0% | 97.37% |
| TF-IDF + LR | Novel Test | 88.00% | 87.50% | 100.0% | 93.33% |
| TF-IDF + SVM | Known Test | 97.76% | 99.01% | 98.53% | 98.77% |
| TF-IDF + SVM | Novel Test | 96.00% | 95.45% | 100.0% | 97.67% |
| DistilBERT | Known Test | 98.21% | 98.08% | 100.0% | 99.03% |
| DistilBERT | Novel Test | 91.00% | 90.32% | 100.0% | 94.92% |

## Key Findings
- **High In-Distribution Accuracy**: Fine-tuned transformers achieve near-perfect (~99% F1) detection on known attack patterns.
- **Generalization Gap**: Performance drops 4-6% on novel, unseen attack categories (e.g. indirect prompt injections from new sources), highlighting the necessity of continuous attack dataset updating.
