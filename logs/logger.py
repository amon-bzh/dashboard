import logging
import os
from logging.handlers import RotatingFileHandler

from shared.paths import LOG_FILE, ensure_dirs


def get_logger(component: str) -> logging.Logger:
    """Get or create a logger for the specified component.

    Args:
        component: The component name (e.g., 'daemon', 'tui').

    Returns:
        A configured logger with the name 'dashboard.<component>'.

    The logger respects the DASHBOARD_LOG_LEVEL environment variable
    (defaults to 'INFO') and uses a RotatingFileHandler with a 1 MB
    max size and 3 backup files.
    """
    ensure_dirs()
    level_name = os.environ.get("DASHBOARD_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logger = logging.getLogger(f"dashboard.{component}")
    logger.setLevel(level)
    if logger.handlers:
        return logger

    handler = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=3)
    handler.setFormatter(
        logging.Formatter(f"%(asctime)s [{component}] %(levelname)s %(message)s")
    )
    logger.addHandler(handler)
    return logger
