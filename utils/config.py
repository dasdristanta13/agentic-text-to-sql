import configparser
import os
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SystemConfig(BaseModel):
    """System configuration model."""
    default_llm_provider: str = Field("openai")
    max_retries: int = Field(3, gt=0)
    schema_cache_ttl: int = Field(300, gt=0)
    sample_rows: int = Field(3, gt=0)

class LoggingConfig(BaseModel):
    """Logging configuration model."""
    level: str = Field("INFO")
    format: str = Field("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

class AppConfig:
    """Enhanced application configuration loader."""
    
    def __init__(self, config_dir: str = "config"):
        self.config = configparser.ConfigParser(interpolation=None)
        self.config.read([
            os.path.join(config_dir, "settings.ini"),
            os.path.join(config_dir, "prompts.ini")
        ])
        
        self.system = self._load_system_config()
        self.logging = self._load_logging_config()
        self.prompts = self._load_prompts()
        self.llm_config = self._load_llm_config()
    
    def _load_system_config(self) -> SystemConfig:
        """Load and validate system configuration."""
        return SystemConfig(
            **{k: self._parse_value(v) for k, v in self.config.items("system")}
        )
    
    def _load_logging_config(self) -> LoggingConfig:
        """Load and validate logging configuration."""
        return LoggingConfig(
            **{k: v for k, v in self.config.items("logging")}
        )
    
    def _load_prompts(self) -> Dict[str, str]:
        """Load prompt templates."""
        # print("Loading prompts from configuration...")
        # print(f"Available sections: {self.config.sections()}")
        return {section: self.config.get(section, "template") 
                for section in self.config.sections() 
                if section.startswith("prompt_")}
    
    def _load_llm_config(self) -> Dict[str, Any]:
        """Load LLM configuration."""
        llm_config: Dict[str, Any] = {"provider": self.system.default_llm_provider}
        
        # Resolve environment variables in settings
        provider_settings: Dict[str, Any] = {}
        provider_section = f"llm.{llm_config['provider']}"
        
        if provider_section in self.config:
            for key, value in self.config.items(provider_section):
                # Handle environment variable substitution
                if value.startswith("${") and value.endswith("}"):
                    env_var = value[2:-1]
                    provider_settings[key] = os.getenv(env_var, "")
                else:
                    provider_settings[key] = value
        else:
            import logging
            logging.warning(f"LLM provider section [{provider_section}] not found in config. Using empty settings.")

        llm_config["settings"] = provider_settings
        return llm_config
    
    def _parse_value(self, value: str) -> Any:
        """Parse configuration values with type inference."""
        try:
            return eval(value)
        except (NameError, SyntaxError):
            return value
    
    def get_prompt(self, name: str) -> Optional[str]:
        """Get prompt template by name."""
        # print(f"Fetching prompt: prompt_{name}")
        # print(f"Available prompts: {list(self.prompts.keys())}")
        return self.config.get("prompts_text_to_sql", "template")
    
    def update_llm_setting(self, key: str, value: Any):
        """Update LLM configuration setting dynamically"""
        if "settings" not in self.llm_config:
            self.llm_config["settings"] = {}
        self.llm_config["settings"][key] = value