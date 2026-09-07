# Detection Models & Architecture

## Model Overview
The framework implements two baseline classifiers and two transformer-based classifiers:

1. **TF-IDF + Logistic Regression**: Fast linear baseline with n-gram feature extraction.
2. **TF-IDF + Linear SVM**: High-margin linear classifier with strong baseline performance.
3. **DistilBERT Baseline (`distilbert-base-uncased`)**: Fine-tuned 66M parameter transformer providing 99.0% Known Test F1 and 94.9% Novel Test F1.
4. **DeBERTa-v3 (`microsoft/deberta-v3-base`)**: 86M parameter disentangled attention transformer for binary and 5-class security classification.
