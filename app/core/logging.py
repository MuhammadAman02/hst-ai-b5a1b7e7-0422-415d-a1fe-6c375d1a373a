"""
Logging configuration for the Pakistani Bank Fraud Detection System.
Provides structured logging with proper formatting and levels.
"""

import logging
import sys
from typing import Optional
from app.config import settings


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Add color to the log level
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


def setup_logging(
    name: Optional[str] = None,
    level: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Set up logging configuration for the application.
    
    Args:
        name: Logger name (defaults to app name)
        level: Log level (defaults to settings.log_level)
        format_string: Log format (defaults to settings.log_format)
    
    Returns:
        Configured logger instance
    """
    logger_name = name or settings.app_name
    log_level = level or settings.log_level
    log_format = format_string or settings.log_format
    
    # Create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    # Create formatter
    if settings.is_development:
        # Use colored formatter for development
        formatter = ColoredFormatter(log_format)
    else:
        # Use standard formatter for production
        formatter = logging.Formatter(log_format)
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module."""
    return logging.getLogger(f"{settings.app_name}.{name}")


# Global application logger
app_logger = setup_logging()

# Log startup message
app_logger.info(f"🚀 Starting {settings.app_name} v{settings.app_version}")
app_logger.info(f"📍 Environment: {settings.environment}")
app_logger.info(f"🔍 Debug Mode: {settings.debug}")