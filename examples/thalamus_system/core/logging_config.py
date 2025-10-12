#!/usr/bin/env python3
"""
Thalamus Centralized Logging Configuration

Copyright (C) 2025 Mark "Rizzn" Hopkins, Athena Vernal, John Casaretto

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import logging
import logging.config
import os
import sys
from typing import Optional


def setup_logging(
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
    log_file: Optional[str] = None,
    enable_file_logging: bool = False
) -> None:
    """
    Set up centralized logging configuration for the Thalamus application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format ('json' or 'text')
        log_file: Path to log file (if file logging is enabled)
        enable_file_logging: Whether to enable file logging
    """
    # Get configuration from environment variables or use defaults
    log_level = log_level or os.getenv('LOG_LEVEL', 'INFO').upper()
    log_format = log_format or os.getenv('LOG_FORMAT', 'text').lower()
    log_file = log_file or os.getenv('LOG_FILE', 'thalamus.log')
    
    # Validate log level
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if log_level not in valid_levels:
        log_level = 'INFO'
    
    # Validate log format
    if log_format not in ['json', 'text']:
        log_format = 'text'
    
    # Configure formatters
    formatters = {}
    handlers = {}
    
    if log_format == 'json':
        formatters['json'] = {
            'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s", "module": "%(module)s", "function": "%(funcName)s", "line": %(lineno)d}',
            'datefmt': '%Y-%m-%dT%H:%M:%S'
        }
        formatter_name = 'json'
    else:
        formatters['standard'] = {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
        formatter_name = 'standard'
    
    # Configure console handler
    handlers['console'] = {
        'class': 'logging.StreamHandler',
        'level': log_level,
        'formatter': formatter_name,
        'stream': 'ext://sys.stdout'
    }
    
    # Configure file handler if enabled
    if enable_file_logging:
        handlers['file'] = {
            'class': 'logging.FileHandler',
            'level': log_level,
            'formatter': formatter_name,
            'filename': log_file,
            'mode': 'a'
        }
    
    # Create logging configuration
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': formatters,
        'handlers': handlers,
        'root': {
            'level': log_level,
            'handlers': list(handlers.keys())
        }
    }
    
    # Apply configuration
    logging.config.dictConfig(config)
    
    # Log the configuration being used
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {log_level}, Format: {log_format}, File: {log_file if enable_file_logging else 'disabled'}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Convenience function for structured logging
def log_with_context(logger: logging.Logger, level: str, message: str, **context) -> None:
    """
    Log a message with additional context.
    
    Args:
        logger: Logger instance
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: Log message
        **context: Additional context to include in the log
    """
    getattr(logger, level.lower())(message, extra=context)
