import os
import time
import logging
import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from typing import Tuple, Optional
from utils.config import SystemConfig
from utils.security import SecurityUtils
from .base import DatabaseConnector

logger = logging.getLogger(__name__)

class PostgresConnector(DatabaseConnector):
    """PostgreSQL database connector implementation."""
    
    def __init__(
        self, 
        config: SystemConfig,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None
    ):
        """
        Initialize PostgreSQL connector with environment fallback.
        
        Args:
            config: System configuration
            host: Database host (default: DB_HOST)
            port: Database port (default: DB_PORT)
            database: Database name (default: DB_NAME)
            user: Username (default: DB_USER)
            password: Password (default: DB_PASSWORD)
        """
        self.host = host or os.getenv("DB_HOST", "localhost")
        self.port = port or int(os.getenv("DB_PORT", "5432"))
        self.database = database or os.getenv("DB_NAME", "postgres")
        self.user = user or os.getenv("DB_USER", "postgres")
        self.password = password or os.getenv("DB_PASSWORD", "")
        super().__init__(config)
    
    def get_engine(self):
        """Create PostgreSQL engine with connection pooling."""
        conn_str = (
            f"postgresql+psycopg2://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )
        return create_engine(
            conn_str,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30
        )
    
    def _get_raw_schema(self) -> str:
        """Generate schema description with sample data."""
        inspector = inspect(self.engine)
        schema_info = []
        sample_rows = self.config.sample_rows
        
        try:
            for schema_name in inspector.get_schema_names():
                if schema_name in ["information_schema", "pg_catalog"]:
                    continue
                    
                for table_name in inspector.get_table_names(schema=schema_name):
                    if not all(SecurityUtils.safe_identifier(i) 
                              for i in [schema_name, table_name]):
                        logger.warning(f"Skipping unsafe identifier: {schema_name}.{table_name}")
                        continue
                    
                    # Get column information
                    columns = []
                    for col in inspector.get_columns(table_name, schema=schema_name):
                        columns.append(f"{col['name']} ({col['type']})")
                    
                    # Get sample data safely
                    sample_data = ""
                    try:
                        result = self.session.execute(
                            text(f"SELECT * FROM {schema_name}.{table_name} LIMIT :limit"),
                            {"limit": sample_rows}
                        )
                        sample_data = "\n".join(str(dict(row)) for row in result.fetchall())
                    except SQLAlchemyError as e:
                        logger.error(f"Schema sampling error: {str(e)}")
                        sample_data = "Sample data unavailable"
                    
                    schema_info.append(
                        f"Schema: {schema_name}\n"
                        f"Table: {table_name}\n"
                        f"Columns: {', '.join(columns)}\n"
                        f"Sample Rows:\n{sample_data}"
                    )
        except SQLAlchemyError as e:
            logger.critical(f"Schema inspection failed: {str(e)}")
            return "Schema inspection failed"
        
        return "\n\n".join(schema_info)
    
    def execute_query(self, query: str) -> Tuple[pd.DataFrame, Optional[str]]:
        """Execute SQL query safely with error handling."""
        try:
            with self.session.begin():
                result = self.session.execute(text(query))
                df = pd.DataFrame(result.fetchall(), columns=list(result.keys()))
            return df, None
        except SQLAlchemyError as e:
            logger.error(f"Query execution failed: {str(e)}")
            return pd.DataFrame(), f"PostgreSQL Error: {str(e)}"