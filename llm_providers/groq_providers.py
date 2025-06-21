import os
import logging
import time
from groq import Groq
from groq.types.chat import ChatCompletion
from .base import BaseLLMProvider
from typing import Dict, Any

logger = logging.getLogger(__name__)

class GroqLlmProvider(BaseLLMProvider):
    """Groq API LLM provider implementation with enhanced features."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        api_key = config.get("api_key") or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Groq API key is required")
        
        self.client = Groq(api_key=api_key)
        self.model = config.get("model", "llama3-70b-8192")
        self.temperature = float(config.get("temperature", 0.3))
        self.max_tokens = int(config.get("max_tokens", 1024))
        self.top_p = float(config.get("top_p", 1.0))
        self.max_retries = int(config.get("max_retries", 3))
        self.retry_delay = float(config.get("retry_delay", 5.0))
    
    def generate(self, prompt: str, **kwargs) -> str:
        retries = 0
        while retries <= self.max_retries:
            try:
                response: ChatCompletion = self.client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=self.model,
                    temperature=self.temperature,
                    max_tokens=kwargs.get("max_tokens", self.max_tokens),
                    top_p=self.top_p,
                    stop=kwargs.get("stop"),
                    stream=False,
                )
                content = response.choices[0].message.content
                return content.strip() if content is not None else ""
            
            except Exception as e:
                if "rate limit" in str(e).lower() and retries < self.max_retries:
                    logger.warning(f"Rate limit exceeded, retrying in {self.retry_delay}s")
                    time.sleep(self.retry_delay)
                    retries += 1
                    continue
                    
                logger.error(f"Groq generation failed: {str(e)}")
                raise
        
        raise RuntimeError(f"Max retries exceeded ({self.max_retries}) for Groq API")
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> bool:
        return bool(config.get("api_key") or os.getenv("GROQ_API_KEY"))