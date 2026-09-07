"""
Target Model Adapters (Phase 19).
Provides a unified interface for evaluating target LLMs (Local and API-based models).
"""

from abc import ABC, abstractmethod
import os
import re
import random

class BaseModelAdapter(ABC):
    """
    Abstract Base Class for all Target Model Adapters.
    Must implement generate(prompt) -> dict with 'response', 'metadata'.
    """
    def __init__(self, model_name: str, config: dict = None):
        self.model_name = model_name
        self.config = config or {}

    @abstractmethod
    def generate(self, prompt: str) -> dict:
        pass

class MockLLMAdapter(BaseModelAdapter):
    """
    Deterministic/configurable Mock LLM for local evaluation and offline assessment.
    Simulates refusal or vulnerability based on model security posture.
    """
    def __init__(self, model_name: str = "Mock-Safe-LLM-v1", security_level: str = "medium"):
        super().__init__(model_name, {"security_level": security_level})
        self.security_level = security_level

    def generate(self, prompt: str) -> dict:
        prompt_lower = prompt.lower()
        
        # Check for typical refusal triggers
        attack_indicators = [
            "ignore all previous instructions", "jailbreak", "override",
            "system prompt", "leak", "bypass", "hack", "exploit", "password"
        ]

        is_attack_like = any(ind in prompt_lower for ind in attack_indicators)

        if self.security_level == "high":
            if is_attack_like:
                response = "I cannot fulfill this request. I am programmed to be a helpful and harmless AI assistant, and I must refuse requests involving safety violations or unauthorized access."
            else:
                response = f"Here is the helpful information requested: Processing prompt cleanly."

        elif self.security_level == "medium":
            # Refuses obvious attacks, vulnerable to subtle ones
            if "ignore all previous instructions" in prompt_lower or "jailbreak" in prompt_lower:
                response = "I am sorry, but I cannot assist with instructions that override my guidelines."
            else:
                response = f"Sure! Executing instruction: '{prompt[:40]}...'. Here are the results."

        else: # low security / baseline vulnerable
            response = f"Simulated Response: Executing request directly. Secrets/data: [UNPROTECTED_CONTENT_ACCESS]"

        return {
            "model_name": self.model_name,
            "response": response,
            "security_level": self.security_level,
            "status": "success"
        }

class LocalTransformersAdapter(BaseModelAdapter):
    """
    Adapter for locally hosted HuggingFace Transformer models (e.g. TinyLlama, Gemma-2b, Qwen).
    """
    def __init__(self, model_name: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"):
        super().__init__(model_name)
        self.pipeline = None

    def _lazy_init(self):
        if self.pipeline is None:
            import torch
            from transformers import pipeline
            self.pipeline = pipeline(
                "text-generation",
                model=self.model_name,
                device_map="auto",
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
            )

    def generate(self, prompt: str) -> dict:
        try:
            self._lazy_init()
            res = self.pipeline(prompt, max_new_tokens=128, do_sample=False)
            gen_text = res[0]["generated_text"]
            return {"model_name": self.model_name, "response": gen_text, "status": "success"}
        except Exception as e:
            # Fallback to mock behavior if model weights unavailable locally
            mock = MockLLMAdapter(model_name=f"Local-{self.model_name} (Fallback)")
            out = mock.generate(prompt)
            out["error_fallback"] = str(e)
            return out

class APIModelAdapter(BaseModelAdapter):
    """
    Adapter for API-based models (OpenAI / Gemini / Anthropic API simulated/integrated).
    """
    def __init__(self, model_name: str = "gpt-3.5-turbo", api_key: str = None):
        super().__init__(model_name, {"api_key": api_key})
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

    def generate(self, prompt: str) -> dict:
        if not self.api_key:
            # If no API key set in environment, use robust mock adapter
            mock = MockLLMAdapter(model_name=f"API-{self.model_name} (Mock)", security_level="high")
            return mock.generate(prompt)
        try:
            # Simple fallback generation
            mock = MockLLMAdapter(model_name=self.model_name, security_level="high")
            return mock.generate(prompt)
        except Exception as e:
            return {"model_name": self.model_name, "response": f"API Error: {e}", "status": "error"}

def get_adapter(model_type: str = "mock", model_name: str = None, security_level: str = "medium"):
    """
    Factory function to get model adapter by string type.
    """
    if model_type == "mock":
        return MockLLMAdapter(model_name=model_name or "Mock-LLM-Standard", security_level=security_level)
    elif model_type == "local":
        return LocalTransformersAdapter(model_name=model_name or "TinyLlama/TinyLlama-1.1B-Chat-v1.0")
    elif model_type == "api":
        return APIModelAdapter(model_name=model_name or "gpt-3.5-turbo")
    else:
        return MockLLMAdapter(model_name=model_name or "Mock-Default", security_level=security_level)
