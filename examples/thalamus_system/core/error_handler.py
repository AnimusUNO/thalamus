#!/usr/bin/env python3
"""
Centralized Error Handling Utilities for Thalamus

This module provides consistent helpers for logging and handling
errors across the codebase.

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

from typing import Any, Optional

from logging_config import get_logger


logger = get_logger(__name__)


def handle_database_error(
    operation: str,
    error: Exception,
    default_return: Optional[Any] = None,
    rethrow: bool = False,
) -> Any:
    """
    Log a database-related error in a consistent format and either rethrow
    or return a default value.

    Args:
        operation: Human-readable operation name (e.g., "init_db").
        error: The caught exception.
        default_return: Value to return when not rethrowing.
        rethrow: If True, re-raise the exception after logging.

    Returns:
        Either raises the exception or returns the provided default value.
    """
    logger.error("Database error in %s: %s", operation, error, exc_info=True)
    if rethrow:
        raise
    return default_return


def handle_api_error(
    operation: str,
    error: Exception,
    rethrow: bool = True,
    default_return: Optional[Any] = None,
) -> Any:
    """
    Log an API/service-related error in a consistent format and either rethrow
    or return a default value.

    Args:
        operation: Human-readable operation name (e.g., "call_openai_text").
        error: The caught exception.
        rethrow: If True (default), re-raise the exception after logging.
        default_return: Value to return when not rethrowing.

    Returns:
        Either raises the exception or returns the provided default value.
    """
    logger.error("API error in %s: %s", operation, error, exc_info=True)
    if rethrow:
        raise
    return default_return
