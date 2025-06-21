import os
import logging
import requests
from .base import BaseLLMProvider
from typing import Dict, Any

logger = logging.getLogger(__name__)

class LlamaLlmProvider(BaseLLMProvider):
    """Llama LLM provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_url = config.get("model_url", "https://api.llama.ai/v1/completions")
        self.api_key = config.get("api_key") or os.getenv("LLAMA_API_KEY")
        if not self.api_key:
            raise ValueError("Llama API key is required")
        
        self.temperature = float(config.get("temperature", 0.7))
        self.max_tokens = int(config.get("max_tokens", 4000))
    
    def generate(self, prompt: str, **kwargs) -> str:
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "prompt": prompt,
                "temperature": self.temperature,
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                **kwargs
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()["choices"][0]["text"].strip()
        except Exception as e:
            logger.error(f"Llama generation failed: {str(e)}")
            raise
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> bool:
        return bool(config.get("api_key") or os.getenv("LLAMA_API_KEY"))