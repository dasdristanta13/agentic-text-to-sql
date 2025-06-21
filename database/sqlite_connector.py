from sqlalchemy import create_engine, inspect, text, Engine
import pandas as pd
from .base import DatabaseConnector
from utils.config import SystemConfig

class SQLiteConnector(DatabaseConnector):
    """SQLite database connector implementation."""
    
    def __init__(
            self, 
            config: SystemConfig,
            db_path: str):
        """
        Initialize SQLite connector.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.engine = self.get_engine()
        super().__init__(config)
    
    def get_engine(self) -> Engine:
        """Create SQLite engine instance."""
        return create_engine(f"sqlite:///{self.db_path}")
    
    def _get_raw_schema(self, sample_rows: int = 3) -> str:
        """Generate schema description with sample data."""
        inspector = inspect(self.engine)
        schema_info = []
        for table_name in inspector.get_table_names():
            # Get column information
            columns = [f"{col['name']} ({col['type']})" for col in inspector.get_columns(table_name)]
            
            # Get sample data
            sample_data = ""
            try:
                with self.engine.connect() as connection:
                    result = connection.execute(text(f"SELECT * FROM {table_name} LIMIT {sample_rows}"))
                    sample_data = "\n".join(str(row) for row in result.fetchall())
            except Exception:
                sample_data = "Unable to fetch sample data"
            
            schema_info.append(
                f"Table: {table_name}\n"
                f"Columns: {', '.join(columns)}\n"
                f"Sample Rows:\n{sample_data}"
            )
        
        return "\n\n".join(schema_info)
    
    def execute_query(self, query: str) -> tuple[pd.DataFrame, str | None]:
        """Execute SQL query safely with error handling."""
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(query))
                df = pd.DataFrame(result.fetchall(), columns=list(result.keys()))
            return df, None
        except Exception as e:
            return pd.DataFrame(), f"SQLite Error: {str(e)}"
        
    def create_sample_data(self):
        """Create sample data for notebook testing"""
        from sqlalchemy import MetaData, Table, Column, Integer, String, Float
        
        metadata = MetaData()
        Table(
            'customers', metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String),
            Column('email', String),
            Column('signup_date', String)
        )
        
        Table(
            'orders', metadata,
            Column('id', Integer, primary_key=True),
            Column('customer_id', Integer),
            Column('product', String),
            Column('amount', Float),
            Column('order_date', String)
        )
        
        metadata.create_all(self.engine)
        
        # Insert sample data
        with self.engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO customers (name, email, signup_date) VALUES
                ('Alice', 'alice@example.com', '2023-01-15'),
                ('Bob', 'bob@example.com', '2023-02-20'),
                ('Charlie', 'charlie@example.com', '2023-03-10')
            """))
            
            conn.execute(text("""
                INSERT INTO orders (customer_id, product, amount, order_date) VALUES
                (1, 'Laptop', 1200.00, '2023-04-01'),
                (1, 'Mouse', 25.99, '2023-04-02'),
                (2, 'Monitor', 350.50, '2023-04-05'),
                (3, 'Keyboard', 89.99, '2023-04-03'),
                (3, 'Headphones', 150.00, '2023-04-04')
            """))
            conn.commit()