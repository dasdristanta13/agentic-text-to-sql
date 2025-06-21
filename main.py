import argparse
import logging
from utils.config import AppConfig
from utils.logging import configure_logging
from database import SQLiteConnector, PostgresConnector, CSVConnector
from system import TextToSQLSystem

def main():
    parser = argparse.ArgumentParser(description="Text-to-SQL Query System")
    parser.add_argument("query", help="Natural language query")
    parser.add_argument("--datasource", choices=["postgres", "sqlite", "csv"], 
                        default="postgres", help="Data source type")
    parser.add_argument("--config", default="config", help="Configuration directory")
    parser.add_argument("--llm", help="Override default LLM provider", 
                        choices=["openai", "azure", "gemini", "llama", "groq"])  # Added groq
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Starting Text-to-SQL Query System")
    
    # Initialize configuration and logging
    config = AppConfig(args.config)
    
    # Override LLM provider if specified
    if args.llm:
        config.system.default_llm_provider = args.llm
    
    configure_logging(config.logging)
    
    # Create connector
    if args.datasource == "postgres":
        connector = PostgresConnector(config.system)
    elif args.datasource == "sqlite":
        connector = SQLiteConnector(config.system, "sales.db")
    elif args.datasource == "csv":
        connector = CSVConnector(config.system, "data.csv", "sales_data")
    else:
        raise ValueError("Invalid datasource type")
    
    # Execute query
    system = TextToSQLSystem(connector, config)
    result = system.run_query(args.query)
    
    # Format output
    print("\n" + "=" * 80)
    print(f"LLM Provider: {config.system.default_llm_provider.upper()}")
    print(f"QUERY: {args.query}")
    print("-" * 80)
    print(f"SQL: {result['sql']}")
    
    if result["result"] is not None and not result["result"].empty:
        print("\nRESULT:")
        print(result["result"].head())
    
    if result["error"]:
        print(f"\nERROR: {result['error']}")
    
    print(f"\nRetries: {result['retries']}")
    print("=" * 80)

if __name__ == "__main__":
    main()