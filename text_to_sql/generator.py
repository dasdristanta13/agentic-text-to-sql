import json
import logging
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from llm_providers import get_llm_provider
from utils.config import AppConfig
from utils.models import LLMOutput

logger = logging.getLogger(__name__)

class TextToSQLGenerator:
    """Generates SQL queries using configurable LLM providers with structured output."""
    
    def __init__(self, db_connector, config: AppConfig):
        self.db_connector = db_connector
        self.config = config
        self.llm_provider = self._create_llm_provider()
        self.prompt_template = self._load_prompt_template()
    
    def _create_llm_provider(self):
        """Initialize LLM provider with JSON mode support"""
        llm_config = self.config.llm_config
        provider_name = llm_config.get("provider", "openai")
        provider_settings = llm_config.get("settings", {})
        
        # Enable JSON mode for supported providers
        if provider_name in ["openai", "groq", "azure"]:
            provider_settings.setdefault("response_format", {"type": "json_object"})
        
        return get_llm_provider(provider_name, provider_settings)
    
    def _load_prompt_template(self) -> str:
        """Load prompt template from configuration."""
        prompt = self.config.get_prompt("text_to_sql")
        if not prompt:
            logger.error("Text-to-SQL prompt template not found!")
            raise ValueError("Missing prompt configuration")
        return prompt
    
    def generate_structured_output(self, question: str, feedback: str = "") -> LLMOutput:
        """
        Generate structured output from natural language question.
        
        Args:
            question: Natural language query
            feedback: Accumulated feedback from previous attempts
            
        Returns:
            LLMOutput: Structured output from LLM
        """
        try:
            # Prepare prompt with feedback
            schema = self.db_connector.get_schema()
            full_prompt = self.prompt_template.format(
                question=question,
                schema=schema,
                feedback=f"Previous Error Feedback:\n{feedback}" if feedback else ""
            )
            
            # Generate output
            raw_output = self.llm_provider.generate(full_prompt)
            
            # Parse structured output
            return LLMOutput.from_text(raw_output)
        except Exception as e:
            logger.error(f"Structured generation failed: {str(e)}")
            return LLMOutput(
                think="Error during reasoning",
                sql_query="",
                explanation="Failed to generate SQL"
            )