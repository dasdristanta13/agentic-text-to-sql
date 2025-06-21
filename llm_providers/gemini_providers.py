import os
import logging
from google import genai
from .base import BaseLLMProvider
from typing import Dict, Any

logger = logging.getLogger(__name__)

class GeminiLlmProvider(BaseLLMProvider):
    """Google Gemini LLM provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        api_key = config.get("api_key") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Gemini API key is required")
        
        client = genai.Client(api_key=api_key)
        self.model = config.get("model", "gemini-pro")
        self.temperature = float(config.get("temperature", 0.2))
        
        # Configure safety settings
        safety_settings = config.get("safety_settings", {})
        self.safety_settings = [
            {"category": cat, "threshold": thr}
            for setting in safety_settings.split(";")
            for cat, thr in [setting.split(":")]
        ] if safety_settings else None
    
    def generate(self, prompt: str, **kwargs) -> str:
        try:
            model = genai.GenerativeModel(self.model)
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=kwargs.get("max_tokens", 500)
                ),
                safety_settings=self.safety_settings
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini generation failed: {str(e)}")
            raise
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> bool:
        return bool(config.get("api_key") or os.getenv("GEMINI_API_KEY"))