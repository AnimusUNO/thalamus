#!/usr/bin/env python3
"""
Thalamus Response Utilities

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

from datetime import datetime
from typing import Dict, Any, Tuple, Optional


def create_success_response(message: str, data: Optional[Dict[str, Any]] = None, status_code: int = 200) -> Tuple[Dict[str, Any], int]:
    """Create a standardized success response."""
    response = {
        "status": "success",
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    if data:
        response["data"] = data
    return response, status_code


def create_error_response(message: str, status_code: int, details: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], int]:
    """Create a standardized error response."""
    response = {
        "error": message,
        "status_code": status_code,
        "timestamp": datetime.utcnow().isoformat()
    }
    if details:
        response["details"] = details
    return response, status_code


def create_validation_error_response(message: str, field_errors: Optional[Dict[str, str]] = None) -> Tuple[Dict[str, Any], int]:
    """Create a validation error response (422 Unprocessable Entity)."""
    details = {"field_errors": field_errors} if field_errors else None
    return create_error_response(message, 422, details)
