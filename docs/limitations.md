# Framework Limitations & Scope Constraints

## Known Limitations
1. **Multimodal Attack Surface**: Current detectors specialize in text-based prompts. Vision (OCR), audio (ASR), and binary document payloads require frontend extraction preprocessing.
2. **Heuristic Refusal Boundaries**: Response evaluation relies on regex and score heuristics. Advanced refusal disguises may require an LLM-as-a-judge evaluator for 100% precision.
3. **Hardware & Memory Requirements**: Transformer fine-tuning requires 8GB+ GPU RAM or CPU fallback with reduced batch sizes.
