# LLM Security Literature Review (2025-2026)

This document compiles 14 state-of-the-art research papers published in 2025 and 2026. These papers validate the approaches taken in this framework (such as using external transformer detectors) and outline the future scope of Agentic and Multimodal LLM security.

### Systematic Reviews & Taxonomies
1. **A Systematic Literature Review on LLM Defenses Against Prompt Injection and Jailbreaking: Expanding NIST Taxonomy** (Jan 2026)
   * *Summary:* Provides a comprehensive review of 88 studies, extending the official NIST adversarial machine learning taxonomy and cataloging defensive strategies.
2. **Jailbreaking LLMs & VLMs: Mechanisms, Evaluation, and Unified Defenses** (Jan 2026)
   * *Summary:* A broad survey covering both Text and Vision-Language Models (VLMs), proposing a unified three-dimensional framework across Attack, Defense, and Evaluation.
3. **The Art of the Jailbreak** (May 2026)
   * *Summary:* Introduces OPTIMUS, a training-free jailbreak evaluator, and provides a massive compositional dataset with 114,000 adversarial prompts for red-teaming.

### Detection & Defense Techniques
4. **ALERT: Zero-shot LLM Jailbreak Detection via Internal Discrepancy Amplification** (Jan 2026)
   * *Summary:* Proposes a novel framework that magnifies internal feature discrepancies between benign and jailbreak prompts to perform zero-shot detection without needing pre-existing templates.
5. **Detecting Jailbreak Attempts in Clinical Training LLMs Through Automated Linguistic Feature Extraction** (Feb 2026)
   * *Summary:* Details a method using BERT-based models (similar to DeBERTa) to extract linguistic features and classify them to determine the likelihood of a jailbreak.
6. **Evaluation of Prompt Injection Defenses in Large Language Models** (Apr 2026)
   * *Summary:* Compares multiple defense configurations, concluding that external output filtering (enforced in application code) is significantly more reliable than relying on an LLM to self-protect.
7. **SecAlign: Preference Optimization for Fundamental Model Hardening** (2026)
   * *Summary:* Explores structural and algorithmic defenses using preference optimization to fundamentally harden base models against prompt manipulation.
8. **The Vulnerability of LLM Rankers to Prompt Injection Attacks** (Feb 2026)
   * *Summary:* Focuses on jailbreak attacks against LLM-based ranking pipelines, assessing how injections can hijack decision objectives in pairwise and listwise ranking paradigms.

### Agentic AI & Indirect Attacks
9. **The Landscape of Prompt Injection Threats in LLM Agents** (Feb 2026)
   * *Summary:* Introduces the *AgentPI* benchmark to evaluate agent behavior under context-dependent interactions, proving that autonomous systems are uniquely vulnerable.
10. **Assessing Automated Prompt Injection Attacks in Agentic Environments** (Jun 2026)
    * *Summary:* Evaluates indirect prompt injections using white-box and black-box attack methods within the AgentDojo framework, highlighting severe vulnerabilities in agentic systems.
11. **Agent Security Bench (ASB)** (2026)
    * *Summary:* A comprehensive benchmarking framework that formalizes attacks and defenses specifically designed for tool-integrated LLM agents.
12. **InjecAgent: Benchmarking Indirect Prompt Injections in Tool-Integrated Agents** (2025/2026)
    * *Summary:* Focuses exclusively on Indirect Prompt Injection (IPI) where malicious instructions are hidden in external sources (web pages, files) that the agent reads.
13. **NRT-Bench: A Benchmark for Multi-turn Red Teaming of LLM Agents** (2026)
    * *Summary:* Emphasizes multi-turn interactions and adaptive red-teaming strategies that evolve during the attack, moving away from static one-off prompt testing.
14. **Multilingual Hidden Prompt Injection Attacks on LLM-Based Academic Reviewing** (Dec 2025)
    * *Summary:* Demonstrates how hidden adversarial prompts embedded in documents can manipulate AI-based peer review scores, noting performance differences across languages.
