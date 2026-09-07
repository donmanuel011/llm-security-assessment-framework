# Dataset Processing & Pipeline

## Overview
The dataset contains 1,984 prompt samples sourced from benchmark security datasets and curated entries.

## Dataset Sources
- **HarmBench**: Standardized jailbreak and harmful prompt benchmarks.
- **PIBench**: Direct and indirect prompt injection benchmarks.
- **Tensor Trust**: Prompt leakage and bank extraction challenges.
- **JailbreakBench**: Behavioral jailbreak triggers and baseline benign controls.

## Data Pipeline Phases
1. **Acquisition (Phase 1)**: Downloads raw benchmark CSV/JSON datasets.
2. **Inspection & Normalization (Phases 2-3)**: Maps fields into unified schema (`prompt`, `label`, `attack_type`).
3. **Cleaning & Deduplication (Phases 4-6)**: Removes empty prompts and computes MinHash LSH similarity for within-source and cross-source deduplication.
4. **Taxonomy Mapping (Phase 7)**: Maps heterogeneous labels into 5 unified categories.
5. **Difficulty Classification (Phase 8)**: Tags samples as `Easy`, `Medium`, `Hard`, or `Novel`.
6. **Leakage-Aware Split (Phase 12)**: 70% Train, 15% Val, 10% Known Test, 5% Novel Test.
