"""
Utilities for Jupyter Notebook integration
"""
import os
import logging
from dotenv import load_dotenv
from utils.config import AppConfig
from utils.logging import configure_logging
from database import SQLiteConnector, PostgresConnector, CSVConnector
from system import TextToSQLSystem
from typing import List

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG_DIR = "./config"
DEFAULT_LOG_LEVEL = "INFO"

class NotebookSystem:
    """Simplified interface for notebook testing"""
    
    def __init__(self, datasource="sqlite", llm_provider="groq", config_dir=None):
        """
        Initialize testing system
        
        Args:
            datasource: 'sqlite', 'postgres', or 'csv'
            llm_provider: 'groq', 'openai', 'azure', 'gemini', or 'llama'
            config_dir: Path to config directory
        """
        # Load environment variables
        load_dotenv()
        
        # Setup configuration
        self.config_dir = config_dir or DEFAULT_CONFIG_DIR
        self.config = AppConfig(self.config_dir)
        self.config.system.default_llm_provider = llm_provider
        
        # Configure logging
        self.config.logging.level = DEFAULT_LOG_LEVEL
        configure_logging(self.config.logging)
        
        # Initialize database connector
        if datasource == "sqlite":
            self.db_connector = SQLiteConnector(
                self.config.system, 
                "sample.db"  # Default sample database
            )
        elif datasource == "postgres":
            self.db_connector = PostgresConnector(
                self.config.system,
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", 5432)),
                database=os.getenv("DB_NAME", "testdb"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", "")
            )
        elif datasource == "csv":
            self.db_connector = CSVConnector(
                self.config.system,
                "sample.csv",  # Default sample CSV
                "data_table"
            )
        else:
            raise ValueError(f"Unknown datasource: {datasource}")
        
        # Initialize system
        self.system = TextToSQLSystem(self.db_connector, self.config)
    
    def run_query(self, question):
        """
        Execute a natural language query
        
        Args:
            question: Natural language question
            
        Returns:
            dict: Result dictionary with keys:
                - sql: Generated SQL
                - result: DataFrame with results
                - error: Error message if any
                - retries: Number of retries
        """
        return self.system.run_query(question)
    
    def set_llm_provider(self, provider):
        """Dynamically change LLM provider"""
        self.config.system.default_llm_provider = provider
        # Reinitialize system to apply changes
        self.system = TextToSQLSystem(self.db_connector, self.config)
    
    def set_model(self, model):
        """Set specific model for current provider"""
        provider = self.config.system.default_llm_provider
        self.config.llm_config["settings"]["model"] = model
        # Reinitialize system to apply changes
        self.system = TextToSQLSystem(self.db_connector, self.config)
    
    def available_models(self):
        """Return available models for current provider"""
        provider = self.config.system.default_llm_provider
        models = {
            # "groq": ["qwen/qwen3-32b","llama-3.1-8b-instant","deepseek-r1-distill-llama-70b"],
            "groq": ["llama-3.1-8b-instant"],
            # "openai": ["gpt-3.5-turbo-instruct", "gpt-4", "gpt-4-turbo"],
            # "azure": ["gpt-35-turbo", "gpt-4"],
            # "gemini": ["gemini-pro", "gemini-1.5-pro"],
            # "llama": ["llama2-13b", "llama2-70b"]
        }
        return models.get(provider, [])
    
    def create_sample_data(self):
        """Create sample database with demo data"""
        if isinstance(self.db_connector, SQLiteConnector):
            self.db_connector.create_sample_data()
            print("Created sample SQLite database")
        else:
            print("Sample data creation only supported for SQLite")
# Add this method to NotebookSystem class
    def run_query_with_history(self, question: str) -> List[dict]:
        """Run query and return all intermediate states for analysis"""
        from text_to_sql.state import AgentState
        
        # Reset feedback for new query
        # self.system.generator.feedback = ""  # Removed: 'feedback' attribute does not exist
        
        states = []
        current_state = AgentState(
            question=question,
            think="",
            sql_query="",
            explanation="",
            query_result=None,
            error="",
            feedback="",
            retry_count=0,
            valid_sql=False
        )
        
        # Manually step through workflow
        try:
            for node in ["generate", "validate", "execute", "handle_error"]:
                new_state = self.system.workflow.nodes[node].invoke(current_state)
                states.append(new_state)
                
                # Break if we've reached end or max retries
                if node == "execute" and not new_state.error:
                    break
                if node == "handle_error" and "Max retries" in new_state.error:
                    break
                    
                current_state = new_state
        except Exception as e:
            logger.error(f"Step-through failed: {str(e)}")
        
        return states


if __name__ == "__main__":
    import os
    load_dotenv()

    # Initialize system
    system = NotebookSystem(
        datasource="sqlite",
        llm_provider="groq",
        config_dir="config"  # Path to config folder
    )

    # Run query with history
    history = system.run_query_with_history(
        "Show total sales per customer"
    )
# Display retry history
    for i, state in enumerate(history):
        print(f"\n{'='*40}")
        print(f"Attempt {i+1} State:")
        print(f"Think: {state['think'][:200]}...")
        print(f"SQL: {state['sql_query'][:100]}...")
        print(f"Explanation: {state['explanation'][:100]}...")
        if state['error']:
            print(f"Error: {state['error'][:200]}...")
        if state:
            print(f"Results: {len(state)} rows")