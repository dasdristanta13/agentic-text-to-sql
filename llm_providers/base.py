from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize LLM provider with configuration.
        
        Args:
            config: Provider-specific configuration
        """
        self.config = config
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text from prompt.
        
        Args:
            prompt: Input prompt text
            
        Returns:
            Generated text output
        """
        pass
    
    @classmethod
    @abstractmethod
    def validate_config(cls, config: Dict[str, Any]) -> bool:
        """
        Validate provider configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass