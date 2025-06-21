import os
import logging
from openai import AzureOpenAI
from .base import BaseLLMProvider
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AzureLlmProvider(BaseLLMProvider):
    """Azure OpenAI LLM provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        api_key = config.get("api_key") or os.getenv("AZURE_API_KEY")
        api_base = config.get("api_base") or os.getenv("AZURE_API_BASE")
        
        if not api_key or not api_base:
            raise ValueError("Azure API key and base URL are required")
        
        self.client = AzureOpenAI(
            api_key=api_key,
            api_version=config.get("api_version", "2023-05-15"),
            azure_endpoint=api_base
        )
        self.deployment = config["deployment_name"]
        self.temperature = float(config.get("temperature", 0))
    
    def generate(self, prompt: str, **kwargs) -> str:
        try:
            response = self.client.completions.create(
                model=self.deployment,
                prompt=prompt,
                temperature=self.temperature,
                max_tokens=kwargs.get("max_tokens", 500),
                **kwargs
            )
            return response.choices[0].text.strip()
        except Exception as e:
            logger.error(f"Azure OpenAI generation failed: {str(e)}")
            raise
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> bool:
        return bool(
            (config.get("api_key") or os.getenv("AZURE_API_KEY")) and
            (config.get("api_base") or os.getenv("AZURE_API_BASE"))
        )