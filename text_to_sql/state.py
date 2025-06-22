from dataclasses import dataclass, field
from pydantic import BaseModel, Field
import pandas as pd
from typing import Optional

# working version 1
# @dataclass
# class AgentState:
#     """State container for the Text-to-SQL workflow."""
#     question: str
#     sql_query: str = ""
#     query_result: pd.DataFrame = field(default_factory=pd.DataFrame)
#     error: str = ""
#     retry_count: int = 0
#     valid_sql: bool = False
    
    
#     def to_dict(self) -> dict:
#         """Serialize state to dictionary for LangGraph."""
#         return {
#             "question": self.question,
#             "sql_query": self.sql_query,
#             "query_result": self.query_result.to_json() if not self.query_result.empty else "",
#             "error": self.error,
#             "retry_count": self.retry_count,
#             "valid_sql": self.valid_sql
#         }
    
#     @classmethod
#     def from_dict(cls, state_dict: dict):
#         df = pd.read_json(state_dict["query_result"]) if state_dict.get("query_result") else pd.DataFrame()
#         return cls(
#             question=state_dict["question"],
#             sql_query=state_dict.get("sql_query", ""),
#             query_result=df,
#             error=state_dict.get("error", ""),
#             retry_count=state_dict.get("retry_count", 0),
#             valid_sql=state_dict.get("valid_sql", False)
#         )

class AgentState(BaseModel):
    """State container for the Text-to-SQL workflow."""
    question: str = Field(..., description="Natural language query from user")
    think: str = Field("", description="Step-by-step reasoning")
    sql_query: str = Field("", description="Generated SQL query")
    explanation: str = Field("", description="Explanation of the SQL query")
    query_result: Optional[pd.DataFrame] = Field(None, description="Query execution result")
    error: str = Field("", description="Error message if any")
    feedback: str = Field("", description="Accumulated feedback for retries")
    retry_count: int = Field(0, description="Number of retry attempts")
    valid_sql: bool = Field(False, description="Flag indicating if SQL is valid")

    class Config:
        arbitrary_types_allowed = True  # Allows pandas DataFrame
        
    def to_dict(self) -> dict:
        return {
            "question": self.question,
            "think": self.think,
            "sql_query": self.sql_query,
            "explanation": self.explanation,
            "query_result": self.query_result.to_json() if self.query_result is not None else "",
            "error": self.error,
            "feedback": self.feedback,
            "retry_count": self.retry_count,
            "valid_sql": self.valid_sql
        }
    
    @classmethod
    def from_dict(cls, state_dict: dict) -> "AgentState":
        query_result = None
        if state_dict.get("query_result"):
            query_result = pd.read_json(state_dict["query_result"])
            
        return cls(
            question=state_dict["question"],
            think=state_dict.get("think", ""),
            sql_query=state_dict.get("sql_query", ""),
            explanation=state_dict.get("explanation", ""),
            query_result=query_result,
            error=state_dict.get("error", ""),
            feedback=state_dict.get("feedback", ""),
            retry_count=state_dict.get("retry_count", 0),
            valid_sql=state_dict.get("valid_sql", False)
        )