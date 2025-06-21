import logging
from text_to_sql.workflow import WorkflowBuilder
from text_to_sql.state import AgentState
from database.base import DatabaseConnector
from utils.config import AppConfig
from text_to_sql.generator import TextToSQLGenerator

logger = logging.getLogger(__name__)

class TextToSQLSystem:
    """Orchestrates the complete Text-to-SQL workflow."""
    
    def __init__(self, db_connector: DatabaseConnector, config: AppConfig):
        self.db_connector = db_connector
        self.config = config
        
        # Initialize components
        self.generator = TextToSQLGenerator(db_connector, config)
        self.workflow = WorkflowBuilder(db_connector, self.generator, config).build()
    
    def run_query(self, question: str) -> dict:
        """Execute full Text-to-SQL workflow."""
        logger.info(f"Processing query: {question[:50]}...")
        initial_state = AgentState(question=question)
        
        try:
            logger.info("Starting workflow execution...")
            result = self.workflow.invoke(initial_state.to_dict())
            final_state = AgentState.from_dict(result)
            
            return {
                "sql": final_state.sql_query,
                "result": final_state.query_result,
                "error": final_state.error,
                "retries": final_state.retry_count
            }
        except Exception as e:
            logger.exception("Workflow execution failed")
            return {
                "sql": "",
                "result": None,
                "error": f"System Error: {str(e)}",
                "retries": 0
            }
        finally:
            self.db_connector.close()