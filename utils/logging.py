import logging
import sys
from utils.config import LoggingConfig

def configure_logging(config: LoggingConfig):
    """Configure application logging."""
    logging.basicConfig(
        level=config.level,
        format=config.format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("text_to_sql.log")
        ]
    )
    
    # Configure SQLAlchemy logging
    sql_logger = logging.getLogger('sqlalchemy')
    sql_logger.setLevel(logging.WARNING)
    
    # Configure OpenAI logging
    openai_logger = logging.getLogger('openai')
    openai_logger.setLevel(logging.INFO)