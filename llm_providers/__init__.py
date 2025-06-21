from .openai_providers import OpenAILlmProvider
from .azure_providers import AzureLlmProvider
# from .gemini_providers import GeminiLlmProvider
from .llama_providers import LlamaLlmProvider
from .base import BaseLLMProvider
from .groq_providers import GroqLlmProvider


PROVIDER_MAP = {
    "openai": OpenAILlmProvider,
    "azure": AzureLlmProvider,
    # "gemini": GeminiLlmProvider,
    "llama": LlamaLlmProvider,
    "groq": GroqLlmProvider,
}

def get_llm_provider(provider_name: str, config: dict) -> BaseLLMProvider:
    """
    Factory function to create LLM provider instances.
    
    Args:
        provider_name: Name of the provider (e.g., 'openai', 'azure')
        config: Provider-specific configuration
        
    Returns:
        BaseLLMProvider instance
    """
    provider_class = PROVIDER_MAP.get(provider_name.lower())
    if not provider_class:
        raise ValueError(f"Unsupported LLM provider: {provider_name}")
    
    if not provider_class.validate_config(config):
        raise ValueError(f"Invalid configuration for provider: {provider_name}")
    
    return provider_class(config)