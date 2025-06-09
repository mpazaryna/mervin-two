"""
Logging configuration for MCP Learning Server
"""

import logging
import sys
from typing import Optional
from logging.handlers import RotatingFileHandler


def setup_logger(
    name: str = "mcp_server",
    level: str = "INFO",
    format_string: Optional[str] = None,
    log_file: Optional[str] = None,
    log_max_size: int = 10 * 1024 * 1024,  # 10MB
    log_backup_count: int = 5
) -> logging.Logger:
    """
    Setup and configure logger for the MCP server.

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string for log messages
        log_file: Optional path to log file for file logging
        log_max_size: Maximum size of log file before rotation (bytes)
        log_backup_count: Number of backup log files to keep

    Returns:
        Configured logger instance
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create formatter
    formatter = logging.Formatter(format_string)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Create file handler if log_file is specified
    if log_file:
        try:
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=log_max_size,
                backupCount=log_backup_count
            )
            file_handler.setLevel(getattr(logging, level.upper()))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            # If file logging fails, log the error to console but continue
            logger.error(f"Failed to setup file logging to {log_file}: {e}")

    return logger


def get_logger(name: str = "mcp_server") -> logging.Logger:
    """
    Get an existing logger or create a new one with default configuration.
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger
