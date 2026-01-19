"""
Logging configuration for graang.

This module provides centralized logging configuration for the entire application.
"""

import logging
import sys
from typing import Optional


# Default log format
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
SIMPLE_FORMAT = "%(levelname)s: %(message)s"


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    format_string: str = SIMPLE_FORMAT
) -> logging.Logger:
    """
    Configure logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to write logs to
        format_string: Log message format string

    Returns:
        logging.Logger: Configured root logger
    """
    # Get root logger
    logger = logging.getLogger("graang")
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(format_string)

    # Console handler (stdout for INFO and below, stderr for WARNING and above)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(lambda record: record.levelno < logging.WARNING)
    logger.addHandler(console_handler)

    # Console handler for warnings and errors (stderr)
    error_handler = logging.StreamHandler(sys.stderr)
    error_handler.setLevel(logging.WARNING)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    # File handler (if specified)
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)  # Log everything to file
            file_handler.setFormatter(logging.Formatter(DEFAULT_FORMAT))
            logger.addHandler(file_handler)
        except (OSError, IOError) as e:
            logger.warning(f"Could not create log file '{log_file}': {e}")

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Name of the module (typically __name__)

    Returns:
        logging.Logger: Logger instance for the module
    """
    return logging.getLogger(f"graang.{name}")


# Configure default logging on module import
_default_logger = setup_logging()
