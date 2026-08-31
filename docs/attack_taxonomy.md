# LLM Attack Taxonomy

This project categorizes LLM inputs into benign and adversarial classes for security assessment.

## 1. Benign Prompt

Normal user input that does not attempt to bypass, manipulate, or compromise the intended behavior of the LLM.

**Classification:** Benign

## 2. Prompt Injection

An attack that attempts to manipulate the instructions followed by an LLM by inserting malicious or conflicting instructions into the input.

**Classification:** Prompt Injection

## 3. Jailbreak

An adversarial technique designed to bypass an LLM's safety restrictions or alignment mechanisms and make the model produce responses that it would normally refuse.

**Classification:** Jailbreak

## 4. Indirect Prompt Injection

An attack in which malicious instructions are embedded within external or untrusted content that an LLM is asked to process.

Potential sources include:

- Web pages
- Documents
- Emails
- Retrieved knowledge
- External data sources

**Classification:** Indirect Prompt Injection

## 5. Prompt Leakage

An attempt to extract hidden system instructions, internal prompts, configuration details, or other information that should not be revealed to the user.

**Classification:** Prompt Leakage

# Classification Structure

LLM Input
    |
    +-- Benign
    |
    +-- Adversarial
          |
          +-- Prompt Injection
          |
          +-- Jailbreak
          |
          +-- Indirect Prompt Injection
          |
          +-- Prompt Leakage

# Assessment Perspective

The framework evaluates attacks at two stages:

1. **Pre-execution:** AI-based detection and classification of the incoming prompt.
2. **Post-execution:** Evaluation of the LLM response to determine whether the attack was successful.

This allows the framework to measure both attack detection capability and LLM robustness.
