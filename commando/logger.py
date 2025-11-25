"""
Logging configuration and utilities.
"""

import logging
import sys
from enum import Enum
from pathlib import Path

from commando.config import Config


class LogLevel(Enum):
    """Logging levels."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


_loggers = {}


def setup_logging(level: LogLevel = None):
    """
    Set up logging configuration.
    
    Args:
        level: Logging level. If None, reads from config.
    """
    config = Config()
    if level is None:
        level_name = config.get("logging.level", "INFO")
        level = LogLevel[level_name.upper()]
    
    # Create logs directory in cache (logs are temporary/cacheable)
    # Following XDG standards, logs should go in cache directory
    log_dir = Path(config.get_cache_dir()) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level.value)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level.value)
    console_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)
    
    # File handler
    log_file = log_dir / "commando.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)  # Always log everything to file
    file_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    )
    file_handler.setFormatter(file_format)
    root_logger.addHandler(file_handler)
    
    logging.info(f"Logging initialized at level {level.name}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    if name not in _loggers:
        _loggers[name] = logging.getLogger(name)
    return _loggers[name]


def set_log_level(level: LogLevel):
    """
    Change the logging level at runtime.
    
    Args:
        level: New logging level
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level.value)
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
            handler.setLevel(level.value)
    logging.info(f"Log level changed to {level.name}")

