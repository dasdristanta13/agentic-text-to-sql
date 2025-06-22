import logging
import time
from langgraph.graph import END, StateGraph
from text_to_sql.state import AgentState
from utils.config import AppConfig
from utils.sql_validation import SQLValidator
from typing import Any, List
from database.base import DatabaseConnector

logger = logging.getLogger(__name__)

class WorkflowBuilder:
    """Builds and configures the Text-to-SQL workflow with structured output."""
    
    def __init__(self, db_connector, generator, config: AppConfig):
        self.db_connector = db_connector
        self.generator = generator
        self.config = config
        self.max_retries = config.system.max_retries
        self.validator = SQLValidator(
            allowed_tables=self._get_allowed_tables()
        )
    
    def _get_allowed_tables(self) -> List[str]:
        """Get list of tables from database schema"""
        try:
            from sqlalchemy import inspect
            inspector = inspect(self.db_connector.engine)
            return inspector.get_table_names()
        except Exception:
            return []
    
    def build(self) -> Any:
        """Construct and compile the workflow graph."""
        workflow = StateGraph(AgentState)
        
        # Add workflow nodes
        workflow.add_node("generate", self._generate_node)
        workflow.add_node("validate", self._validate_node)
        workflow.add_node("execute", self._execute_node)
        workflow.add_node("handle_error", self._error_handler_node)
        
        # Define workflow structure
        workflow.set_entry_point("generate")
        workflow.add_edge("generate", "validate")
        
        # Conditional edges after validation
        workflow.add_conditional_edges(
            "validate",
            lambda state: "execute" if state.valid_sql else "handle_error",
            {"execute": "execute", "handle_error": "handle_error"}
        )
        
        # Conditional edges after execution
        workflow.add_conditional_edges(
            "execute",
            lambda state: "handle_error" if state.error else END,
            {"handle_error": "handle_error", END: END}
        )
        
        # Conditional edges for error handling
        workflow.add_conditional_edges(
            "handle_error",
            self._should_retry,
            {"generate": "generate", END: END}
        )
        
        return workflow.compile()
    
    def _generate_node(self, state: AgentState) -> dict:
        """Generate structured output with reasoning and SQL"""
        try:
            start_time = time.time()
            output = self.generator.generate_structured_output(
                state.question,
                feedback=state.feedback
            )
            latency = time.time() - start_time
            
            logger.info(f"Generated output in {latency:.2f}s")
            logger.debug(f"Think: {output.think[:100]}...")
            logger.debug(f"SQL: {output.sql_query[:100]}...")
            
            return {
                "think": output.think,
                "sql_query": output.sql_query,
                "explanation": output.explanation,
                "error": "",
                "valid_sql": False  # Needs validation
            }
        except Exception as e:
            logger.error(f"Generation failed: {str(e)}")
            return {
                "error": f"Generation Error: {str(e)}",
                "feedback": state.feedback
            }
    
    def _validate_node(self, state: AgentState) -> dict:
        """Validate generated SQL structure"""
        if not state.sql_query.strip():
            return {
                "error": "Empty SQL query",
                "valid_sql": False,
                "feedback": state.feedback + "\n- Generated SQL was empty"
            }
        
        try:
            # Validate SQL structure
            parsed = self.validator.validate(state.sql_query)
            logger.debug("SQL validation passed")
            return {
                "valid_sql": True,
                "error": "",
                "feedback": state.feedback
            }
        except Exception as e:
            error_msg = f"Validation Error: {str(e)}"
            logger.warning(error_msg)
            return {
                "error": error_msg,
                "valid_sql": False,
                "feedback": state.feedback + f"\n- Validation failed: {str(e)}"
            }
    
    def _execute_node(self, state: AgentState) -> dict:
        """Execute SQL query against database"""
        try:
            start_time = time.time()
            result, error = self.db_connector.execute_query(state.sql_query)
            latency = time.time() - start_time
            
            if error:
                logger.warning(f"Execution failed in {latency:.2f}s: {error}")
                return {
                    "error": f"Execution Error: {error}",
                    "feedback": state.feedback + f"\n- Execution failed: {error}",
                    "query_result": None
                }
            
            logger.info(f"Query executed in {latency:.2f}s, returned {len(result)} rows")
            return {
                "query_result": result,
                "error": "",
                "feedback": state.feedback
            }
        except Exception as e:
            logger.error(f"Execution crashed: {str(e)}")
            return {
                "error": f"Execution Error: {str(e)}",
                "feedback": state.feedback + f"\n- Execution crashed: {str(e)}",
                "query_result": None
            }
    
    def _error_handler_node(self, state: AgentState) -> dict:
        """Prepare feedback for retry"""
        if state.retry_count < self.max_retries:
            feedback = (
                f"## Attempt {state.retry_count + 1} Feedback ##\n"
                f"Previous Error: {state.error}\n"
                f"Generated SQL: {state.sql_query}\n"
                f"Explanation: {state.explanation}\n"
                f"Reasoning: {state.think}\n"
                "Please fix these issues in the next attempt."
            )
            
            logger.warning(f"Retry #{state.retry_count + 1} for: {state.error[:100]}")
            return {
                "feedback": feedback,
                "retry_count": state.retry_count + 1
            }
        
        logger.error(f"Max retries exceeded for: {state.error[:100]}")
        return {
            "error": f"Max retries exceeded ({self.max_retries} attempts)",
            "feedback": state.feedback
        }
    
    def _should_retry(self, state: AgentState) -> str:
        """Determine if retry is possible"""
        if state.retry_count < self.max_retries and "Retry" not in state.error:
            return "generate"
        return END