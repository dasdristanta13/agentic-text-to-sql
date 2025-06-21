import os
import logging
from openai import OpenAI
from .base import BaseLLMProvider
from typing import Dict, Any

logger = logging.getLogger(__name__)

class OpenAILlmProvider(BaseLLMProvider):
    """OpenAI LLM provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        api_key = config.get("api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = OpenAI(api_key=api_key)
        self.model = config.get("model", "gpt-3.5-turbo-instruct")
        self.temperature = float(config.get("temperature", 0))
    
    def generate(self, prompt: str, **kwargs) -> str:
        try:
            response = self.client.completions.create(
                model=self.model,
                prompt=prompt,
                temperature=self.temperature,
                max_tokens=kwargs.get("max_tokens", 500),
                **kwargs
            )
            return response.choices[0].text.strip()
        except Exception as e:
            logger.error(f"OpenAI generation failed: {str(e)}")
            raise
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> bool:
        return bool(config.get("api_key") or os.getenv("OPENAI_API_KEY"))