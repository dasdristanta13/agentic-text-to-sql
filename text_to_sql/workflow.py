import logging
import time
from langgraph.graph import END, StateGraph
from text_to_sql.state import AgentState
from text_to_sql.generator import TextToSQLGenerator
from database.base import DatabaseConnector
from utils.config import AppConfig
from typing import Any

logger = logging.getLogger(__name__)

class WorkflowBuilder:
    """Builds and configures the Text-to-SQL workflow."""
    
    def __init__(self, db_connector: DatabaseConnector, generator: TextToSQLGenerator, config: AppConfig):
        self.db_connector = db_connector
        self.generator = generator
        self.config = config
        self.max_retries = config.system.max_retries
    
    def build(self) -> Any:
        """Construct and compile the workflow graph."""
        workflow = StateGraph(AgentState)
        
        # Add workflow nodes
        workflow.add_node("generate_sql", self._generate_sql_node)
        workflow.add_node("execute_query", self._execute_query_node)
        workflow.add_node("handle_error", self._error_handler_node)
        
        # Define workflow structure
        workflow.set_entry_point("generate_sql")
        workflow.add_edge("generate_sql", "execute_query")
        
        # Conditional edges
        workflow.add_conditional_edges(
            "execute_query",
            self._should_handle_error,
            {"handle_error": "handle_error", END: END}
        )
        
        workflow.add_conditional_edges(
            "handle_error",
            self._should_retry,
            {"generate_sql": "generate_sql", END: END}
        )
        
        return workflow.compile()
    
    def _generate_sql_node(self, state: AgentState) -> dict:
        """Node: Generate SQL from natural language question."""
        try:
            start_time = time.time()
            sql_query = self.generator.generate_sql(state.question)
            latency = time.time() - start_time
            
            logger.info(f"Generated SQL in {latency:.2f}s: {sql_query[:100]}...")
            return {"sql_query": sql_query, "error": "", "question": state.question}
        except Exception as e:
            logger.error(f"SQL generation failed: {str(e)}")
            return {"error": f"Generation Error: {str(e)}", "question": state.question}
    
    def _execute_query_node(self, state: AgentState) -> dict:
        """Node: Execute SQL query against database."""
        if not state.sql_query.strip():
            return {"error": "Empty SQL query", "question": state.question}
        
        try:
            start_time = time.time()
            result, error = self.db_connector.execute_query(state.sql_query)
            latency = time.time() - start_time
            
            if error:
                logger.warning(f"Query failed in {latency:.2f}s: {error}")
                return {"error": error, "question": state.question}
            
            logger.info(f"Query executed in {latency:.2f}s, returned {len(result)} rows")
            return {"query_result": result, "error": "", "question": state.question}
        except Exception as e:
            logger.error(f"Query execution crashed: {str(e)}")
            return {"error": f"Execution Error: {str(e)}", "question": state.question}
    
    def _error_handler_node(self, state: AgentState) -> dict:
        """Node: Handle errors and decide retry strategy."""
        if state.retry_count < self.max_retries:
            logger.warning(f"Retry #{state.retry_count + 1} for: {state.error[:100]}")
            return {
                "error": f"Retry #{state.retry_count + 1}: {state.error}",
                "retry_count": state.retry_count + 1,
                "question": state.question
            }
        logger.error(f"Max retries exceeded for: {state.error[:100]}")
        return {"error": f"Max retries exceeded ({self.max_retries} attempts)", "question": state.question}
    
    def _should_handle_error(self, state: AgentState) -> str:
        """Determine if error handling is needed."""
        return "handle_error" if state.error else END
    
    def _should_retry(self, state: AgentState) -> str:
        """Determine if retry is possible."""
        if state.retry_count <= self.max_retries and "Retry" in state.error:
            return "generate_sql"
        return END