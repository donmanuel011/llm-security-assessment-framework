"""
Preflight Heuristic Scanner (Phase 20)
Provides early-stage detection of obfuscated, encoded, and structurally malicious prompts
before passing them to the heavy ML detector models.
"""

import math
import re

class PreflightScanner:
    def __init__(self):
        # Known indicators of agent exploitation / exfiltration
        self.agent_patterns = [
            re.compile(r"!\[.*?\]\(http[s]?://.*?\)", re.IGNORECASE), # Markdown image exfil
            re.compile(r"curl\s+-X\s+(POST|GET)", re.IGNORECASE),     # Command injection
            re.compile(r"<(script|iframe|svg).*?>", re.IGNORECASE),   # XSS / HTML injection
            re.compile(r"system_prompt", re.IGNORECASE),              # System prompt fishing
            re.compile(r"repeat\s+the\s+(words|text)\s+above", re.IGNORECASE), # Leakage extraction
        ]
        
        # Base64 regex (matches strings of 16+ valid base64 chars with padding)
        self.base64_pattern = re.compile(r"^(?:[A-Za-z0-9+/]{4}){4,}(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$")
        # Hex regex
        self.hex_pattern = re.compile(r"^(?:[0-9a-fA-F]{2}\s*){8,}$")
        
    def shannon_entropy(self, text: str) -> float:
        """Calculate Shannon Entropy of a string to detect obfuscation."""
        if not text:
            return 0.0
        entropy = 0.0
        length = len(text)
        char_counts = {}
        for char in text:
            char_counts[char] = char_counts.get(char, 0) + 1
        for count in char_counts.values():
            p = count / length
            entropy -= p * math.log2(p)
        return entropy

    def scan(self, prompt: str) -> dict:
        """
        Fast heuristic scan of the prompt.
        Returns a dict: {"flagged": bool, "reason": str, "risk_multiplier": float}
        """
        prompt_stripped = prompt.strip()
        
        # 1. Structural / Agent Pattern Check
        for pattern in self.agent_patterns:
            if pattern.search(prompt_stripped):
                return {
                    "flagged": True, 
                    "reason": "Agent-Exploit/Exfiltration Signature Detected",
                    "risk_multiplier": 1.5 # Increases risk score significantly
                }

        # 2. Obfuscation / Encoding Check (Regex)
        # Check if a substantial part of the text looks like raw base64 or hex
        words = prompt_stripped.split()
        for word in words:
            if len(word) > 20 and self.base64_pattern.match(word):
                return {
                    "flagged": True,
                    "reason": "Base64 Obfuscation Detected",
                    "risk_multiplier": 1.2
                }
            if len(word) > 16 and self.hex_pattern.match(word):
                return {
                    "flagged": True,
                    "reason": "Hex Obfuscation Detected",
                    "risk_multiplier": 1.2
                }

        # 3. Entropy Check
        # Normal English text entropy is usually around 3.5 to 5.0
        # Highly obfuscated text (random characters) or dense code can exceed 5.5
        ent = self.shannon_entropy(prompt_stripped)
        if ent > 5.5 and len(prompt_stripped) > 50:
            # We don't necessarily flag it as completely blocked, but we raise suspicion
            # For demonstration, we'll flag extreme entropy (e.g., > 6.0) as outright obfuscation
            if ent > 6.0:
                return {
                    "flagged": True,
                    "reason": f"High Entropy Obfuscation Detected (Score: {ent:.2f})",
                    "risk_multiplier": 1.3
                }

        # If nothing triggered
        return {
            "flagged": False,
            "reason": "Clean (Passed Heuristics)",
            "risk_multiplier": 1.0
        }
