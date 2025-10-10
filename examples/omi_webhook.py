#!/usr/bin/env python3
"""
Thalamus OMI Webhook Server

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

from flask import Flask, request
from typing import Tuple, Dict, Any
import json
import logging
from response_utils import create_success_response, create_error_response, create_validation_error_response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route("/omi", methods=["POST"])
def omi_webhook() -> Tuple[Dict[str, Any], int]:
    """Process incoming webhook data with proper HTTP status codes."""
    logger.info(f"Incoming POST: {request.method} {request.url}")
    
    try:
        # Validate content type
        if not request.is_json:
            return create_error_response("Content-Type must be application/json", 400)
        
        # Parse JSON data
        try:
            data = request.get_json(force=True)
        except json.JSONDecodeError as e:
            return create_error_response("Invalid JSON format", 400, {"json_error": str(e)})
        
        # Validate required fields
        field_errors = {}
        
        if not data:
            return create_error_response("Request body cannot be empty", 400)
        
        if not data.get('session_id'):
            field_errors['session_id'] = "session_id is required"
        
        if not data.get('segments'):
            field_errors['segments'] = "segments array is required"
        elif not isinstance(data.get('segments'), list):
            field_errors['segments'] = "segments must be an array"
        elif len(data.get('segments', [])) == 0:
            field_errors['segments'] = "segments array cannot be empty"
        
        if not data.get('log_timestamp'):
            field_errors['log_timestamp'] = "log_timestamp is required"
        
        if field_errors:
            return create_validation_error_response("Validation failed", field_errors)
        
        # Log successful data reception
        logger.info("Successfully received webhook data", extra={
            "session_id": data.get('session_id'),
            "segment_count": len(data.get('segments', [])),
            "timestamp": data.get('log_timestamp')
        })
        
        # TODO: Process the data (integrate with thalamus_app.py process_event function)
        # For now, just acknowledge receipt
        logger.debug("Webhook data received successfully")
        
        return create_success_response(
            "Data received and processed successfully",
            {
                "session_id": data.get('session_id'),
                "segments_processed": len(data.get('segments', [])),
                "timestamp": data.get('log_timestamp')
            }
        )
        
    except Exception as e:
        logger.error(f"Unexpected error processing webhook: {e}", exc_info=True)
        return create_error_response("Internal server error", 500, {"error_type": type(e).__name__})

@app.route("/ping", methods=["GET"])
def ping() -> Tuple[Dict[str, Any], int]:
    """Health check endpoint."""
    return create_success_response("Service is healthy", {"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
