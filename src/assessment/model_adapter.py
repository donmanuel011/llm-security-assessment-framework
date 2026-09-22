"""
Target Model Adapters (Phase 19).
Provides a unified interface for evaluating target LLMs (Local and API-based models).
"""

from abc import ABC, abstractmethod
import os
import re
import random
import requests
import json

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
    Adapter for OpenAI API-based models and OpenAI-compatible endpoints (vLLM, LM Studio, Together, DeepSeek).
    """
    def __init__(self, model_name: str = "gpt-3.5-turbo", api_key: str = None, api_base: str = None):
        super().__init__(model_name, {"api_key": api_key, "api_base": api_base})
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.api_base = api_base

    def generate(self, prompt: str) -> dict:
        if not self.api_key and not self.api_base:
            mock = MockLLMAdapter(model_name=f"API-{self.model_name} (Mock)", security_level="high")
            return mock.generate(prompt)
        try:
            import openai
            
            client_args = {}
            if self.api_key:
                client_args["api_key"] = self.api_key
            else:
                client_args["api_key"] = "not-needed" # Some local servers need a dummy key
                
            if self.api_base:
                client_args["base_url"] = self.api_base
                
            client = openai.OpenAI(**client_args)
            resp = client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=256
            )
            response_text = resp.choices[0].message.content
            return {"model_name": self.model_name, "response": response_text, "status": "success"}
        except Exception as e:
            return {"model_name": self.model_name, "response": f"API Error: {e}", "status": "error"}


class GeminiAdapter(BaseModelAdapter):
    """
    Adapter for Google Gemini API using the new google-genai SDK.
    Free tier: https://aistudio.google.com/app/apikey
    Set env var: GEMINI_API_KEY=your_key  (in the same CMD session)
    Or pass --api-key argument.

    Usage:
        set GEMINI_API_KEY=your_key
        venv\\Scripts\\python.exe src/assessment/assessment_engine.py --target gemini --sample-size 20 2>nul
    """
    def __init__(self, model_name: str = "gemini-2.0-flash-lite", api_key: str = None):
        super().__init__(model_name)
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

    def generate(self, prompt: str) -> dict:
        if not self.api_key:
            return {
                "model_name": self.model_name,
                "response": "[ERROR] GEMINI_API_KEY not set. "
                            "Get a free key at https://aistudio.google.com/app/apikey "
                            "then run:  set GEMINI_API_KEY=your_key",
                "status": "error"
            }
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=self.api_key)
            resp = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(max_output_tokens=256)
            )
            # Check if blocked by safety filters
            candidate = resp.candidates[0] if resp.candidates else None
            if not candidate:
                response_text = "[BLOCKED by Gemini Safety Filters]"
            elif hasattr(candidate, 'finish_reason') and str(candidate.finish_reason) in ("SAFETY", "FinishReason.SAFETY", "2"):
                response_text = "[REFUSED - SAFETY]"
            else:
                response_text = resp.text if resp.text else "[BLOCKED by Gemini Safety Filters]"
            return {"model_name": self.model_name, "response": response_text, "status": "success"}
        except Exception as e:
            return {"model_name": self.model_name, "response": f"Gemini API Error: {e}", "status": "error"}


class GroqAdapter(BaseModelAdapter):
    """
    Adapter for Groq-hosted models (Llama 3.3, Mixtral, Gemma, etc.).
    Groq offers a generous free tier — get a key at https://console.groq.com

    Default model: qwen/qwen3.8-27b (since llama-3.3-70b-versatile is restricted)

    Usage:
        set GROQ_API_KEY=your_key
        python scan.py -t groq -n 25
        python scan.py -t groq --model qwen/qwen3.8-27b -n 25
    """
    def __init__(self, model_name: str = "qwen/qwen3.8-27b", api_key: str = None):
        super().__init__(model_name)
        self.api_key = api_key or os.getenv("GROQ_API_KEY")

    def generate(self, prompt: str) -> dict:
        if not self.api_key:
            return {
                "model_name": self.model_name,
                "response": (
                    "[ERROR] GROQ_API_KEY not set. "
                    "Get a free key at https://console.groq.com "
                    "then run:  set GROQ_API_KEY=your_key"
                ),
                "status": "error"
            }
        try:
            from groq import Groq
            client = Groq(api_key=self.api_key)
            resp = client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=256,
                temperature=0.0,  # deterministic for reproducible security testing
            )
            response_text = resp.choices[0].message.content or ""
            return {"model_name": self.model_name, "response": response_text, "status": "success"}
        except Exception as e:
            return {"model_name": self.model_name, "response": f"Groq API Error: {e}", "status": "error"}


class OllamaAdapter(BaseModelAdapter):
    """
    Adapter for locally hosted Ollama models.
    """
    def __init__(self, model_name: str = "llama3", api_base: str = "http://localhost:11434"):
        super().__init__(model_name)
        self.api_base = api_base.rstrip("/")

    def generate(self, prompt: str) -> dict:
        try:
            url = f"{self.api_base}/api/generate"
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.0}
            }
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            response_text = response.json().get("response", "")
            return {"model_name": self.model_name, "response": response_text, "status": "success"}
        except Exception as e:
            return {"model_name": self.model_name, "response": f"Ollama Error: {e}", "status": "error"}


class CustomRESTAdapter(BaseModelAdapter):
    """
    Adapter for arbitrary REST APIs configured via JSON.
    """
    def __init__(self, model_name: str = "custom", config_path: str = None):
        super().__init__(model_name)
        self.config_path = config_path
        self.custom_config = {}
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                self.custom_config = json.load(f)

    def generate(self, prompt: str) -> dict:
        if not self.custom_config:
            return {"model_name": self.model_name, "response": "[ERROR] No valid custom config provided.", "status": "error"}
        
        try:
            url = self.custom_config.get("url")
            headers = self.custom_config.get("headers", {})
            payload_template = json.dumps(self.custom_config.get("payload", {}))
            
            # Inject prompt into template safely
            escaped_prompt = json.dumps(prompt)[1:-1] # Remove surrounding quotes
            payload_str = payload_template.replace("{{prompt}}", escaped_prompt)
            payload = json.loads(payload_str)
            
            method = self.custom_config.get("method", "POST").upper()
            
            if method == "POST":
                response = requests.post(url, headers=headers, json=payload, timeout=60)
            else:
                response = requests.get(url, headers=headers, params=payload, timeout=60)
                
            response.raise_for_status()
            
            # Extract response based on json_path
            resp_json = response.json()
            json_path = self.custom_config.get("response_json_path", "")
            
            if json_path:
                keys = json_path.split(".")
                extracted = resp_json
                for k in keys:
                    if isinstance(extracted, list):
                        extracted = extracted[int(k)]
                    else:
                        extracted = extracted.get(k, {})
                response_text = str(extracted)
            else:
                response_text = str(resp_json)
                
            return {"model_name": self.model_name, "response": response_text, "status": "success"}
        except Exception as e:
            return {"model_name": self.model_name, "response": f"Custom REST Error: {e}", "status": "error"}


def _infer_adapter_type(model_name: str) -> str:
    """Infer the correct adapter type based on the model name string."""
    if not model_name:
        return "mock"
    
    name_lower = model_name.lower()
    
    if "gemini" in name_lower:
        return "gemini"
    
    if name_lower.startswith("gpt") or name_lower.startswith("o1") or name_lower.startswith("o3"):
        return "api"
        
    groq_keywords = ["llama", "mixtral", "gemma", "qwen", "deepseek"]
    if any(k in name_lower for k in groq_keywords):
        # We don't auto-infer Ollama because it overlaps with Groq/Local models by name. 
        # User should explicitly specify target=ollama.
        if os.getenv("GROQ_API_KEY"):
            return "groq"
        return "local"
        
    return "mock"

def get_adapter(model_type: str = "auto", model_name: str = None,
                security_level: str = "medium", api_key: str = None,
                api_base: str = None, custom_config: str = None):
    """
    Factory function to get model adapter by string type.
    Supported types: auto | mock | local | api | gemini | groq | ollama | custom
    """
    if model_type == "auto" or not model_type:
        model_type = _infer_adapter_type(model_name)

    if model_type == "mock":
        return MockLLMAdapter(model_name=model_name or "Mock-LLM-Standard", security_level=security_level)
    elif model_type == "local":
        return LocalTransformersAdapter(model_name=model_name or "TinyLlama/TinyLlama-1.1B-Chat-v1.0")
    elif model_type == "gemini":
        return GeminiAdapter(model_name=model_name or "gemini-2.0-flash-lite", api_key=api_key)
    elif model_type == "api":
        return APIModelAdapter(model_name=model_name or "gpt-3.5-turbo", api_key=api_key, api_base=api_base)
    elif model_type == "groq":
        return GroqAdapter(model_name=model_name or "qwen/qwen3.8-27b", api_key=api_key)
    elif model_type == "ollama":
        base_url = api_base or "http://localhost:11434"
        return OllamaAdapter(model_name=model_name or "llama3", api_base=base_url)
    elif model_type == "custom":
        return CustomRESTAdapter(model_name=model_name or "custom", config_path=custom_config)
    else:
        return MockLLMAdapter(model_name=model_name or "Mock-Default", security_level=security_level)
