import pandas as pd
from sqlalchemy import create_engine, Engine, text
from .base import DatabaseConnector
from utils.config import SystemConfig

class CSVConnector(DatabaseConnector):
    """CSV file connector implementation (uses in-memory SQLite)."""
    
    def __init__(
            self, 
            config: SystemConfig,
            csv_path: str, 
            table_name: str = "data"):
        """
        Initialize CSV connector.
        
        Args:
            csv_path: Path to CSV file
            table_name: Name to use for the SQL table
        """
        self.csv_path = csv_path
        self.table_name = table_name
        self.df = pd.read_csv(csv_path)
        self.engine = create_engine("sqlite:///:memory:")
        self.df.to_sql(table_name, self.engine, index=False, if_exists="replace")
        super().__init__(config)
    
    def get_engine(self) -> Engine:
        """Get in-memory SQLite engine."""
        return self.engine
    
    def _get_raw_schema(self, sample_rows: int = 3) -> str:
        """Generate schema description with sample data."""
        return (
            f"Table: {self.table_name}\n"
            f"Columns: {', '.join(self.df.columns)}\n"
            f"Sample Rows:\n{self.df.head(sample_rows).to_string(index=False)}"
        )
    
    def execute_query(self, query: str) -> tuple[pd.DataFrame, str | None]:
        """Execute SQL query on in-memory database."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                return pd.DataFrame(result.fetchall(), columns=list(result.keys())), None
        except Exception as e:
            return pd.DataFrame(), f"CSV Connector Error: {str(e)}"