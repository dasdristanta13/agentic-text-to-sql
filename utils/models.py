from pydantic import BaseModel, Field
import re
from typing import Optional
import json

class LLMOutput(BaseModel):
    """Structured output from LLM"""
    think: str = Field(..., description="Step-by-step reasoning process")
    sql_query: str = Field(..., description="Generated SQL query")
    explanation: str = Field(..., description="Explanation of the SQL query")
    
    @classmethod
    def from_text(cls, text: str) -> "LLMOutput":
        """Parse structured output from text"""
        try:
            # Try parsing as JSON first
            data = json.loads(text.strip())
            return cls(**data)
        except json.JSONDecodeError:
            # Fallback to pattern matching
            return cls.parse_unstructured(text)
    
    @classmethod
    def parse_unstructured(cls, text: str) -> "LLMOutput":
        """Parse unstructured output using pattern matching"""
        think_part = ""
        sql_part = ""
        explanation_part = ""
        
        # Common patterns
        patterns = [
            r"THINK:\s*(?P<think>.+?)\s*(SQL QUERY:|SQL:|EXPLANATION:|$)",
            r"SQL QUERY:\s*(?P<sql>.+?)\s*(EXPLANATION:|$)",
            r"EXPLANATION:\s*(?P<explanation>.+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                if 'think' in match.groupdict() and match.group('think'):
                    think_part = match.group('think').strip()
                if 'sql' in match.groupdict() and match.group('sql'):
                    sql_part = match.group('sql').strip()
                if 'explanation' in match.groupdict() and match.group('explanation'):
                    explanation_part = match.group('explanation').strip()
        
        return cls(
            think=think_part or "No reasoning provided",
            sql_query=sql_part or "",
            explanation=explanation_part or "No explanation provided"
        )