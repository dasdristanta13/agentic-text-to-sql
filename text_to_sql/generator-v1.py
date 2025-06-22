import logging
from langchain.prompts import PromptTemplate
from llm_providers import get_llm_provider
from utils.config import AppConfig

logger = logging.getLogger(__name__)

class TextToSQLGenerator:
    """Generates SQL queries using configurable LLM providers."""
    
    def __init__(self, db_connector, config: AppConfig):
        """
        Initialize SQL generator.
        
        Args:
            db_connector: Database connector instance
            config: Application configuration
        """
        self.db_connector = db_connector
        self.config = config
        
        # Initialize LLM provider
        llm_config = self.config.llm_config
        provider_name = llm_config.get("provider", "openai")
        provider_settings = llm_config.get("settings", {})
        
        self.llm_provider = get_llm_provider(
            provider_name, 
            provider_settings
        )
        
        # Initialize prompt
        self.prompt_template = self._load_prompt_template()
    
    def _load_prompt_template(self) -> str:
        """Load prompt template from configuration."""
        print("Loading text-to-SQL prompt template...")
        prompt = self.config.get_prompt("text_to_sql")
        if not prompt:
            logger.error("Text-to-SQL prompt template not found!")
            raise ValueError("Missing prompt configuration")
        return prompt
    
    def generate_sql(self, question: str,feedback: str = "") -> str:
        """
        Generate SQL query with optional feedback from validation
        
        Args:
            question: Natural language query
            feedback: Validation feedback from previous attempt
            
        Returns:
            str: Generated SQL query
        """
        try:
            # Prepare prompt
            schema = self.db_connector.get_schema()
            full_prompt = self.prompt_template.format(
                question=question,
                schema=schema
            )
            if feedback:
                full_prompt += (
                "\n\nPrevious attempt failed validation. Please correct these issues:"
                f"\n{feedback}"
                "\n\nRevised SQL Query:"
            )
            
            # Generate SQL
            return self.llm_provider.generate(full_prompt)
        except Exception as e:
            logger.error(f"SQL generation failed: {str(e)}")
            raise