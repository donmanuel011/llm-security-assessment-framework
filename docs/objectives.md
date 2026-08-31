# Objectives

## 1. Dataset Creation and Preparation

- Collect and integrate adversarial prompt data from established datasets such as HarmBench and PIBench along with benign prompts.
- Clean, normalize, deduplicate, and categorize prompts according to defined attack types.
- Develop a standardized dataset suitable for training and evaluating the AI-based detection model.

## 2. AI-Based Attack Detection

- Develop an AI-based prompt classification model using transformer architectures such as BERT or DeBERTa.
- Classify inputs into benign and adversarial categories such as prompt injection and jailbreak.
- Evaluate the detector using accuracy, precision, recall, F1-score, and confusion matrix.

## 3. Automated LLM Security Assessment

- Develop an automated framework for testing LLMs using diverse adversarial prompts.
- Evaluate model responses to determine whether attacks succeed or are appropriately refused.
- Measure security performance across different attack categories and target LLMs.

## 4. Risk Assessment and Reporting

- Calculate security metrics including Attack Success Rate (ASR), refusal rate, and detection performance.
- Develop a risk scoring mechanism to identify high-risk attack scenarios.
- Generate security reports and visualizations highlighting vulnerabilities, model performance, and potential mitigation areas.
