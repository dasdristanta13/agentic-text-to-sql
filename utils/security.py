import re
from typing import Optional

class SecurityUtils:
    """Security utilities for SQL operations."""
    
    SAFE_IDENTIFIER = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
    
    @classmethod
    def safe_identifier(cls, identifier: str) -> bool:
        """Check if identifier is safe for SQL."""
        return bool(cls.SAFE_IDENTIFIER.match(identifier))
    
    @classmethod
    def sanitize_sql(cls, sql: str) -> str:
        """Basic SQL sanitization (for display only, not execution)."""
        return re.sub(r'[\s\n]+', ' ', sql).strip()