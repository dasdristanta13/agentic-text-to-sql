from pydantic import BaseModel, field_validator, ValidationError
from typing import List, Optional
import re
import sqlparse
from sqlparse.sql import Identifier, IdentifierList

class SQLColumn(BaseModel):
    name: str
    table: Optional[str] = None
    alias: Optional[str] = None

class SQLTable(BaseModel):
    name: str
    alias: Optional[str] = None

class SQLQuery(BaseModel):
    command: str
    columns: List[SQLColumn]
    tables: List[SQLTable]
    where_clause: Optional[str] = None
    group_by: Optional[List[SQLColumn]] = None
    having_clause: Optional[str] = None
    order_by: Optional[List[SQLColumn]] = None
    limit: Optional[int] = None

    @field_validator('command')
    @classmethod
    def command_must_be_select(cls, v: str) -> str:
        if v.lower() != "select":
            raise ValueError("Only SELECT queries are allowed")
        return v.lower()

    @field_validator('columns', mode='after')
    @classmethod
    def validate_columns(cls, cols: List[SQLColumn]) -> List[SQLColumn]:
        pattern = re.compile(r'[;\\-]{2,}|\/\*|\*\/', re.IGNORECASE)
        for c in cols:
            if pattern.search(c.name):
                raise ValueError(f"Invalid column name: {c.name}")
        return cols

    @field_validator('tables', mode='after')
    @classmethod
    def validate_tables(cls, tables: List[SQLTable]) -> List[SQLTable]:
        pattern = re.compile(r'[;\\-]{2,}|\/\*|\*\/', re.IGNORECASE)
        for t in tables:
            if pattern.search(t.name):
                raise ValueError(f"Invalid table name: {t.name}")
        return tables

    @field_validator('where_clause', 'having_clause', mode='after')
    @classmethod
    def validate_conditions(cls, v: Optional[str]) -> Optional[str]:
        if v and re.search(r'\b(?:drop|delete|update|insert|alter|create|truncate)\b', v, re.IGNORECASE):
            raise ValueError("Dangerous SQL operation detected")
        return v

    @classmethod
    def parse_sql(cls, sql: str) -> "SQLQuery":
        """Parse SQL string into structured components"""
        parsed = sqlparse.parse(sql)[0]
        
        # Extract command type
        command = parsed.get_type().lower()
        
        # Extract columns
        columns = []
        for token in parsed.tokens:
            if isinstance(token, IdentifierList):
                for identifier in token.get_identifiers():
                    columns.append(cls._parse_identifier(identifier))
            elif isinstance(token, Identifier):
                columns.append(cls._parse_identifier(token))
        
        # Extract tables (simplified)
        tables = []
        from_seen = False
        for token in parsed.tokens:
            if token.value.lower() == "from":
                from_seen = True
                continue
            if from_seen and isinstance(token, Identifier):
                tables.append(SQLTable(name=token.get_real_name()))
        
        # Create instance (simplified - real implementation would extract more)
        return cls(
            command=command,
            columns=columns,
            tables=tables
        )
    
    @staticmethod
    def _parse_identifier(identifier) -> SQLColumn:
        """Parse SQL identifier into column model"""
        parts = [t.value for t in identifier.tokens if t.ttype is not None]
        full_name = "".join(parts).strip()
        
        # Handle aliases
        if " as " in full_name.lower():
            name, alias = full_name.lower().split(" as ", 1)
            return SQLColumn(name=name.strip(), alias=alias.strip())
        
        return SQLColumn(name=full_name)

class SQLValidator:
    """Validate and sanitize SQL queries"""
    
    def __init__(self, allowed_tables: List[str]):
        self.allowed_tables = [t.lower() for t in allowed_tables]
    
    def validate(self, sql: str) -> SQLQuery:
        """Validate SQL query structure and content"""
        try:
            # Parse SQL into structured model
            parsed_query = SQLQuery.parse_sql(sql)
            
            # Validate against allowed tables
            for table in parsed_query.tables:
                if table.name.lower() not in self.allowed_tables:
                    raise ValueError(f"Access to table '{table.name}' is not allowed")
            
            # Prevent Cartesian products
            if len(parsed_query.tables) > 1 and not self._has_join_condition(sql):
                raise ValueError("Multi-table queries must include JOIN conditions")
            
            return parsed_query
        except (ValidationError, ValueError) as e:
            raise ValueError(f"SQL validation failed: {str(e)}")
    
    def _has_join_condition(self, sql: str) -> bool:
        """Check if query contains explicit JOIN conditions"""
        sql_lower = sql.lower()
        return any(
            keyword in sql_lower
            for keyword in [" join ", " on ", " using ", " where "]
        )