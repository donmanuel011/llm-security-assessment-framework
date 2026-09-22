# Objectives

## 1. Adversarial Dataset & Taxonomy Alignment
- Integrate established security benchmarks (HarmBench, PIBench, AgentPI) alongside benign conversational logs.
- Align prompt datasets with expanded 2025/2026 adversarial taxonomies to address modern threats, specifically **Indirect Prompt Injections (IPI)** hidden in external documents.
- Clean, normalize, deduplicate, and automatically score the difficulty of attacks.

## 2. External AI-Based Defense Mechanisms
- Develop a robust external prompt classifier using sequence classification transformers (e.g., DeBERTa-v3).
- **Research Alignment:** Recent 2026 literature proves that *external filtering architectures* are significantly more reliable than relying on an LLM for native self-protection.
- Enable zero-shot detection to catch novel, unseen jailbreaks without relying on static attack templates.

## 3. Automated Agentic & LLM Assessment
- Develop an automated execution framework to systematically "red-team" Target LLMs.
- Expand assessment capabilities beyond static chat models to test **Agentic Workflows** (agents with tool/API access).
- Evaluate Target LLM responses to determine whether an attack successfully breached the model's safety guardrails or was appropriately refused.

## 4. Actionable Security Reporting
- Calculate aggregate security metrics including Attack Success Rate (ASR), refusal rate, and detector F1-Score.
- Develop a dynamic Risk Scoring mechanism to quantify vulnerabilities for security operations (SOC) teams.
- Generate interactive visual reports that highlight exposure and guide enterprise mitigation strategies.
