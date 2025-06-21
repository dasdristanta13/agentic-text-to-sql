from dataclasses import dataclass, field
import pandas as pd
from typing import Optional

@dataclass
class AgentState:
    """State container for the Text-to-SQL workflow."""
    question: str
    sql_query: str = ""
    query_result: pd.DataFrame = field(default_factory=pd.DataFrame)
    error: str = ""
    retry_count: int = 0
    
    # def __init__(self, question: str):
    #     """
    #     Initialize agent state with a user question.
        
    #     Args:
    #         question: Natural language query from user
    #     """
    #     self.question = question
    #     self.sql_query = ""  # Generated SQL query
    #     self.query_result = pd.DataFrame()  # Query execution result
    #     self.error = ""  # Error message if any
    #     self.retry_count = 0  # Number of retry attempts
    
    def to_dict(self) -> dict:
        """Serialize state to dictionary for LangGraph."""
        return {
            "question": self.question,
            "sql_query": self.sql_query,
            "query_result": self.query_result.to_json() if not self.query_result.empty else "",
            "error": self.error,
            "retry_count": self.retry_count
        }
    
    @classmethod
    def from_dict(cls, state_dict: dict):
        df = pd.read_json(state_dict["query_result"]) if state_dict.get("query_result") else pd.DataFrame()
        return cls(
            question=state_dict["question"],
            sql_query=state_dict.get("sql_query", ""),
            query_result=df,
            error=state_dict.get("error", ""),
            retry_count=state_dict.get("retry_count", 0)
        )