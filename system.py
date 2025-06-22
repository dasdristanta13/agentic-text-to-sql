import logging
from text_to_sql.workflow import WorkflowBuilder
from text_to_sql.state import AgentState
from text_to_sql.generator import TextToSQLGenerator
from database.base import DatabaseConnector
from utils.config import AppConfig

logger = logging.getLogger(__name__)

class TextToSQLSystem:
    """Orchestrates the complete Text-to-SQL workflow with structured output."""
    
    def __init__(self, db_connector: DatabaseConnector, config: AppConfig):
        self.db_connector = db_connector
        self.config = config
        self.generator = TextToSQLGenerator(db_connector, config)
        self.workflow = WorkflowBuilder(db_connector, self.generator, config).build()
    
    def run_query(self, question: str,) -> dict:
        """Execute full Text-to-SQL workflow."""
        logger.info(f"Processing query: {question[:50]}...")
        # Use self.<variable>_history to persist variables across runs
        if not hasattr(self, "explanation_history"):
            self.explanation_history = ""
        if not hasattr(self, "think_history"):
            self.think_history = ""
        if not hasattr(self, "sql_query_history"):
            self.sql_query_history = ""
        if not hasattr(self, "query_result_history"):
            self.query_result_history = None
        if not hasattr(self, "error_history"):
            self.error_history = ""
        if not hasattr(self, "feedback_history"):
            self.feedback_history = ""
        if not hasattr(self, "retry_count_history"):
            self.retry_count_history = 0

        initial_state = AgentState(
            question=question,
            think=self.think_history,
            sql_query=self.sql_query_history,
            explanation=self.explanation_history,
            query_result=self.query_result_history,
            error=self.error_history,
            feedback=self.feedback_history,
            retry_count=self.retry_count_history,
            valid_sql=False
        )

        try:
            # Execute workflow
            result_state = self.workflow.invoke(initial_state)
            # Update histories for future runs
            self.think_history = result_state.think
            self.sql_query_history = result_state.sql_query
            self.explanation_history = result_state.explanation
            self.query_result_history = result_state.query_result
            self.error_history = result_state.error
            self.feedback_history = result_state.feedback
            self.retry_count_history = result_state.retry_count
            result_state = self.workflow.invoke(initial_state)
            
            # Prepare result
            return {
                "think": result_state.think,
                "sql": result_state.sql_query,
                "explanation": result_state.explanation,
                "result": result_state.query_result,
                "error": result_state.error,
                "feedback": result_state.feedback,
                "retries": result_state.retry_count
            }
        except Exception as e:
            logger.exception("Workflow execution failed")
            return {
                "think": "",
                "sql": "",
                "explanation": "",
                "result": None,
                "error": f"System Error: {str(e)}",
                "feedback": "",
                "retries": 0
            }
        finally:
            try:
                self.db_connector.close()
            except Exception as e:
                logger.error(f"Error closing connection: {str(e)}")