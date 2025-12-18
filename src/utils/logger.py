"""
Logger - Logging Configuration

This module sets up a consistent logging format across the project.
Logs help you understand what the program is doing and debug issues.

Log Levels (from least to most severe):
    DEBUG   - Detailed information for debugging
    INFO    - Confirmation that things are working
    WARNING - Something unexpected, but program continues
    ERROR   - Something failed, but program continues
    CRITICAL - Serious error, program may need to stop

Log Output:
    - Console (stdout) - for immediate feedback
    - File (logs/forecast.log) - for historical record

Usage:
    from src.utils.logger import get_logger
    
    logger = get_logger(__name__)
    logger.info("Starting forecast generation...")
    logger.error("Failed to fetch XML: %s", error_message)
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# Logs directory
LOGS_DIR = Path("logs")

# Log format: timestamp - level - module - message
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(
    name: str = "forecast",
    level: int = logging.INFO,
    log_to_file: bool = True
) -> logging.Logger:
    """
    Set up and return a configured logger.
    
    Args:
        name: Logger name (usually __name__ of the calling module)
        level: Logging level (default: INFO)
        log_to_file: Whether to also log to a file (default: True)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Create formatters
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    
    # === Console Handler ===
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # === File Handler ===
    if log_to_file:
        LOGS_DIR.mkdir(exist_ok=True)
        
        # Log filename includes date for easy organization
        log_filename = f"forecast_{datetime.now().strftime('%Y-%m-%d')}.log"
        file_handler = logging.FileHandler(
            LOGS_DIR / log_filename,
            encoding="utf-8"  # Important for Hebrew text in logs
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    This is a convenience function that returns an existing logger
    or creates a new one with default settings.
    
    Args:
        name: Logger name (typically pass __name__)
        
    Returns:
        Logger instance
        
    Usage:
        logger = get_logger(__name__)
        logger.info("Processing started")
    """
    return setup_logger(name)
