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
import os
import time
from datetime import datetime, UTC
from werkzeug.exceptions import RequestEntityTooLarge, BadRequest
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
from response_utils import create_success_response, create_error_response, create_validation_error_response
from database import get_db
try:
    # Prefer relative import within examples package layout
    from ..thalamus_app.thalamus_app import process_event
except Exception:
    # Fallback when running as a module
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'thalamus_app'))
    from thalamus_app import process_event
from logging_config import setup_logging, get_logger

# Initialize centralized logging
setup_logging()
logger = get_logger(__name__)

# Configure request size limits (configurable via environment variables)
MAX_REQUEST_SIZE_MB = int(os.getenv('MAX_REQUEST_SIZE_MB', '10'))
MAX_JSON_SIZE_MB = int(os.getenv('MAX_JSON_SIZE_MB', '5'))
MAX_REQUEST_SIZE = MAX_REQUEST_SIZE_MB * 1024 * 1024  # Convert to bytes
MAX_JSON_SIZE = MAX_JSON_SIZE_MB * 1024 * 1024  # Convert to bytes

# Application startup time for uptime tracking
START_TIME = time.time()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_REQUEST_SIZE

@app.errorhandler(RequestEntityTooLarge)
def handle_large_request(e) -> Tuple[Dict[str, Any], int]:
    """Handle requests that exceed the size limit."""
    logger.warning(f"Request too large: {request.content_length} bytes (max: {MAX_REQUEST_SIZE} bytes)")
    return create_error_response(
        f"Request too large. Maximum size is {MAX_REQUEST_SIZE_MB}MB",
        413,
        {
            "max_size_mb": MAX_REQUEST_SIZE_MB,
            "received_size_bytes": request.content_length
        }
    )

@app.errorhandler(BadRequest)
def handle_bad_request(e) -> Tuple[Dict[str, Any], int]:
    """Handle bad request errors."""
    logger.warning(f"Bad request: {e}")
    return create_error_response("Bad request", 400, {"error": str(e)})

@app.route("/omi", methods=["POST"])
def omi_webhook() -> Tuple[Dict[str, Any], int]:
    """Process incoming webhook data with proper HTTP status codes."""
    logger.info(f"Incoming POST: {request.method} {request.url}")
    
    # Validate content type
    if not request.is_json:
        return create_error_response("Content-Type must be application/json", 400)
    
    # Parse JSON data with better error handling
    try:
        data = request.get_json(force=True)
    except RequestEntityTooLarge:
        return create_error_response(
            f"Request too large. Maximum size is {MAX_REQUEST_SIZE_MB}MB",
            413,
            {
                "max_size_mb": MAX_REQUEST_SIZE_MB,
                "received_size_bytes": request.content_length
            }
        )
    except Exception as e:
        logger.warning(f"JSON parsing error: {e}")
        return create_error_response("Invalid JSON format", 400, {"json_error": str(e)})
    
    try:
        
        # Additional JSON size validation (beyond Flask's MAX_CONTENT_LENGTH)
        json_str = json.dumps(data) if data else ""
        if len(json_str.encode('utf-8')) > MAX_JSON_SIZE:
            logger.warning(f"JSON payload too large: {len(json_str)} bytes (max: {MAX_JSON_SIZE} bytes)")
            return create_error_response(
                f"JSON payload too large. Maximum size is {MAX_JSON_SIZE_MB}MB",
                413,
                {
                    "max_json_size_mb": MAX_JSON_SIZE_MB,
                    "received_json_size_bytes": len(json_str.encode('utf-8'))
                }
            )
        
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
        
        # Process the data into the database
        try:
            process_event(data)
            logger.debug("Webhook data processed successfully")
            return create_success_response(
                "Data received and processed successfully",
                {
                    "session_id": data.get('session_id'),
                    "segments_processed": len(data.get('segments', [])),
                    "timestamp": data.get('log_timestamp')
                }
            )
        except Exception as e:
            logger.error(f"Error processing webhook data: {e}", exc_info=True)
            # Return 200 to avoid client retries but include error details
            return create_success_response(
                "Data received with processing errors",
                {
                    "session_id": data.get('session_id'),
                    "segments_processed": 0,
                    "timestamp": data.get('log_timestamp'),
                    "processing_error": str(e)
                }
            )
        
    except Exception as e:
        logger.error(f"Unexpected error processing webhook: {e}", exc_info=True)
        return create_error_response("Internal server error", 500, {"error_type": type(e).__name__})

@app.route("/ping", methods=["GET"])
def ping() -> Tuple[Dict[str, Any], int]:
    """Health check endpoint."""
    return create_success_response("Service is healthy", {"status": "ok"})

@app.route("/health", methods=["GET"])
def health_check() -> Tuple[Dict[str, Any], int]:
    """Basic health check endpoint."""
    uptime_seconds = time.time() - START_TIME
    return create_success_response(
        "Service is healthy",
        {
            "status": "healthy",
            "uptime_seconds": uptime_seconds,
            "version": "1.0.0",
            "timestamp": datetime.now(UTC).isoformat()
        }
    )

@app.route("/health/detailed", methods=["GET"])
def detailed_health_check() -> Tuple[Dict[str, Any], int]:
    """Detailed health check with dependency status."""
    health_status = {
        "status": "healthy",
            "timestamp": datetime.now(UTC).isoformat(),
        "version": "1.0.0",
        "uptime_seconds": time.time() - START_TIME,
        "checks": {}
    }
    
    # Database connectivity check
    try:
        with get_db() as conn:
            conn.execute("SELECT 1")
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Environment variables check
    required_env_vars = ["OPENAI_API_KEY"]
    for var in required_env_vars:
        if os.getenv(var):
            health_status["checks"][f"env_{var}"] = "healthy"
        else:
            health_status["checks"][f"env_{var}"] = "unhealthy: not set"
            health_status["status"] = "unhealthy"
    
    # Configuration check
    health_status["checks"]["config"] = {
        "max_request_size_mb": MAX_REQUEST_SIZE_MB,
        "max_json_size_mb": MAX_JSON_SIZE_MB
    }
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return create_success_response("Health check completed", health_status, status_code)

@app.route("/ready", methods=["GET"])
def readiness_check() -> Tuple[Dict[str, Any], int]:
    """Readiness check for service discovery."""
    try:
        # Check database connectivity
        with get_db() as conn:
            conn.execute("SELECT 1")
        
        # Check required environment variables
        required_env_vars = ["OPENAI_API_KEY"]
        missing_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            return create_error_response(
                f"Service not ready: Missing environment variables: {', '.join(missing_vars)}",
                503
            )
        
        return create_success_response("Service is ready", {"status": "ready"})
        
    except Exception as e:
        return create_error_response(f"Service not ready: {str(e)}", 503)

@app.route("/metrics", methods=["GET"])
def metrics() -> Tuple[Dict[str, Any], int]:
    """Basic metrics endpoint for monitoring."""
    uptime_seconds = time.time() - START_TIME
    metrics_data = {
        "uptime_seconds": uptime_seconds,
        "uptime_hours": uptime_seconds / 3600,
        "max_request_size_mb": MAX_REQUEST_SIZE_MB,
        "max_json_size_mb": MAX_JSON_SIZE_MB,
            "timestamp": datetime.now(UTC).isoformat()
    }
    return create_success_response("Metrics retrieved", metrics_data)

if __name__ == "__main__":
    logger.info(f"Starting webhook server with size limits:")
    logger.info(f"  - Max request size: {MAX_REQUEST_SIZE_MB}MB")
    logger.info(f"  - Max JSON size: {MAX_JSON_SIZE_MB}MB")
    app.run(host="0.0.0.0", port=5000)
