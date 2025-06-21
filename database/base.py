from abc import ABC, abstractmethod
import pandas as pd
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from typing import Optional, Tuple
from utils.config import SystemConfig

class DatabaseConnector(ABC):
    """Abstract base class for database connectors."""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.engine = self.get_engine()
        self.session = sessionmaker(bind=self.engine)()
        self._schema_cache = None
        self._cache_time = 0
    
    @abstractmethod
    def get_engine(self) -> Engine:
        """Create and return a SQLAlchemy engine instance."""
        pass
    
    @abstractmethod
    def _get_raw_schema(self) -> str:
        """Generate raw schema description."""
        pass
    
    def get_schema(self, use_cache: bool = True) -> str:
        """Get schema with caching support."""
        if not use_cache or not self._schema_cache:
            self._schema_cache = self._get_raw_schema()
        return self._schema_cache
    
    @abstractmethod
    def execute_query(self, query: str) -> Tuple[pd.DataFrame, Optional[str]]:
        """Execute SQL query and return results."""
        pass
    
    def close(self):
        """Close database connections."""
        if self.session:
            self.session.close()
        if self.engine:
            self.engine.dispose()