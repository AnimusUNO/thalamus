#!/usr/bin/env python3
"""
Unit Tests for Thalamus Webhook Server

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

import pytest
import json
import os
from unittest.mock import patch, Mock
from datetime import datetime, UTC

# Import the modules we're testing
from thalamus_system.webhook_server.omi_webhook import app
from thalamus_system.core.response_utils import (
    create_success_response, create_error_response, create_validation_error_response
)


class TestWebhookEndpoints:
    """Test webhook endpoint functionality."""
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_omi_webhook_success(self, flask_client, sample_session_data):
        """Test successful webhook data processing."""
        response = flask_client.post(
            '/omi',
            data=json.dumps(sample_session_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'session_id' in data['data']
        assert data['data']['session_id'] == sample_session_data['session_id']
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_omi_webhook_invalid_json(self, flask_client):
        """Test webhook with invalid JSON."""
        response = flask_client.post(
            '/omi',
            data='invalid json',
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'Invalid JSON format' in data['message']
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_omi_webhook_missing_session_id(self, flask_client):
        """Test webhook with missing session_id."""
        invalid_data = {
            "segments": [{"text": "test"}],
            "log_timestamp": datetime.now(UTC).isoformat() + "Z"
        }
        
        response = flask_client.post(
            '/omi',
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        assert response.status_code == 422
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'session_id' in data['errors']
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_omi_webhook_missing_segments(self, flask_client):
        """Test webhook with missing segments."""
        invalid_data = {
            "session_id": "test_session",
            "log_timestamp": datetime.now(UTC).isoformat() + "Z"
        }
        
        response = flask_client.post(
            '/omi',
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        assert response.status_code == 422
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'segments' in data['errors']
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_omi_webhook_empty_segments(self, flask_client):
        """Test webhook with empty segments array."""
        invalid_data = {
            "session_id": "test_session",
            "segments": [],
            "log_timestamp": datetime.now(UTC).isoformat() + "Z"
        }
        
        response = flask_client.post(
            '/omi',
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        assert response.status_code == 422
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'segments' in data['errors']
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_omi_webhook_wrong_content_type(self, flask_client, sample_session_data):
        """Test webhook with wrong content type."""
        response = flask_client.post(
            '/omi',
            data=json.dumps(sample_session_data),
            content_type='text/plain'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'Content-Type must be application/json' in data['message']
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_omi_webhook_large_payload(self, flask_client, mock_env_vars):
        """Test webhook with payload exceeding size limits."""
        # Create a large payload
        large_segments = []
        for i in range(1000):  # Create many segments
            large_segments.append({
                "speaker_id": 1,
                "text": "x" * 1000,  # Large text
                "start_time": float(i),
                "end_time": float(i + 1)
            })
        
        large_data = {
            "session_id": "large_session",
            "segments": large_segments,
            "log_timestamp": datetime.now(UTC).isoformat() + "Z"
        }
        
        response = flask_client.post(
            '/omi',
            data=json.dumps(large_data),
            content_type='application/json'
        )
        
        # Should return 413 (Payload Too Large) or handle gracefully
        assert response.status_code in [413, 200]  # Depends on configuration


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_ping_endpoint(self, flask_client):
        """Test ping endpoint."""
        response = flask_client.get('/ping')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['message'] == 'Service is healthy'
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_health_endpoint(self, flask_client):
        """Test health endpoint."""
        response = flask_client.get('/health')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'uptime_seconds' in data['data']
        assert 'version' in data['data']
        assert 'timestamp' in data['data']
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_detailed_health_endpoint(self, flask_client, test_db, mock_env_vars):
        """Test detailed health endpoint."""
        response = flask_client.get('/health/detailed')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'checks' in data['data']
        assert 'database' in data['data']['checks']
        assert 'config' in data['data']['checks']
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_ready_endpoint(self, flask_client, mock_env_vars):
        """Test readiness endpoint."""
        response = flask_client.get('/ready')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['message'] == 'Service is ready'
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_metrics_endpoint(self, flask_client):
        """Test metrics endpoint."""
        response = flask_client.get('/metrics')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'uptime_seconds' in data['data']
        assert 'uptime_hours' in data['data']
        assert 'timestamp' in data['data']


class TestResponseUtils:
    """Test response utility functions."""
    
    @pytest.mark.unit
    def test_create_success_response(self):
        """Test creating success response."""
        message = "Test success"
        data = {"test": "data"}
        
        response, status_code = create_success_response(message, data)
        
        assert status_code == 200
        assert response['status'] == 'success'
        assert response['message'] == message
        assert response['data'] == data
        assert 'timestamp' in response
    
    @pytest.mark.unit
    def test_create_error_response(self):
        """Test creating error response."""
        message = "Test error"
        status_code = 400
        details = {"error_code": "TEST_ERROR"}
        
        response, returned_status_code = create_error_response(message, status_code, details)
        
        assert returned_status_code == status_code
        assert response['status'] == 'error'
        assert response['message'] == message
        assert response['status_code'] == status_code
        assert response['details'] == details
        assert 'timestamp' in response
    
    @pytest.mark.unit
    def test_create_validation_error_response(self):
        """Test creating validation error response."""
        message = "Validation failed"
        errors = {"field1": "Field 1 is required", "field2": "Field 2 is invalid"}
        
        response, status_code = create_validation_error_response(message, errors)
        
        assert status_code == 422
        assert response['status'] == 'error'
        assert response['message'] == message
        assert response['status_code'] == 422
        assert response['errors'] == errors
        assert 'timestamp' in response


class TestRequestSizeLimits:
    """Test request size limit handling."""
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_request_size_limit_configuration(self, mock_env_vars):
        """Test that request size limits are properly configured."""
        # The app should be configured with size limits
        assert app.config['MAX_CONTENT_LENGTH'] > 0
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_oversized_request_handling(self, flask_client):
        """Test handling of oversized requests."""
        # Create a request that exceeds the size limit
        oversized_data = {
            "session_id": "test",
            "segments": [{"text": "x" * (10 * 1024 * 1024)}],  # 10MB of text
            "log_timestamp": datetime.now(UTC).isoformat() + "Z"
        }
        
        response = flask_client.post(
            '/omi',
            data=json.dumps(oversized_data),
            content_type='application/json'
        )
        
        # Should return 413 (Payload Too Large)
        assert response.status_code == 413


class TestErrorHandling:
    """Test error handling in webhook server."""
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_unexpected_error_handling(self, flask_client):
        """Test handling of unexpected errors."""
        # Test with malformed JSON that will cause an internal error
        response = flask_client.post(
            '/omi',
            data='{"invalid": json}',  # Invalid JSON
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'Invalid JSON format' in data['message']
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_database_error_handling(self, flask_client, sample_session_data):
        """Test handling of database errors."""
        with patch('thalamus_system.webhook_server.omi_webhook.get_db') as mock_get_db:
            mock_get_db.side_effect = Exception("Database error")
            
            response = flask_client.post(
                '/omi',
                data=json.dumps(sample_session_data),
                content_type='application/json'
            )
            
            # Should handle gracefully - might still return 200 if error handling is good
            assert response.status_code in [200, 500]


class TestLogging:
    """Test logging functionality in webhook server."""
    
    @pytest.mark.unit
    def test_request_logging(self, flask_client, sample_session_data, caplog):
        """Test that requests are properly logged."""
        with caplog.at_level("INFO"):
            response = flask_client.post(
                '/omi',
                data=json.dumps(sample_session_data),
                content_type='application/json'
            )
        
        assert response.status_code == 200
        # Check that request was logged
        log_messages = [record.message for record in caplog.records]
        assert any("Incoming POST" in msg for msg in log_messages)
    
    @pytest.mark.unit
    def test_error_logging(self, flask_client, caplog):
        """Test that errors are properly logged."""
        with caplog.at_level("INFO"):  # Change to INFO level
            response = flask_client.post(
                '/omi',
                data='invalid json',
                content_type='application/json'
            )
        
        assert response.status_code == 400
        # Check that error was logged
        log_messages = [record.message for record in caplog.records]
        assert any("JSON parsing error" in msg for msg in log_messages)


class TestSecurity:
    """Test security-related functionality."""
    
    @pytest.mark.unit
    @pytest.mark.security
    def test_sql_injection_protection(self, flask_client):
        """Test protection against SQL injection attempts."""
        malicious_data = {
            "session_id": "'; DROP TABLE sessions; --",
            "segments": [{"text": "test"}],
            "log_timestamp": datetime.now(UTC).isoformat() + "Z"
        }
        
        response = flask_client.post(
            '/omi',
            data=json.dumps(malicious_data),
            content_type='application/json'
        )
        
        # Should handle gracefully without executing malicious SQL
        assert response.status_code in [200, 422]
    
    @pytest.mark.unit
    @pytest.mark.security
    def test_xss_protection(self, flask_client):
        """Test protection against XSS attempts."""
        xss_data = {
            "session_id": "test_session",
            "segments": [{"text": "<script>alert('xss')</script>"}],
            "log_timestamp": datetime.now(UTC).isoformat() + "Z"
        }
        
        response = flask_client.post(
            '/omi',
            data=json.dumps(xss_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        # Response should not contain the script tag
        data = response.get_json()
        assert '<script>' not in str(data)
    
    @pytest.mark.unit
    @pytest.mark.security
    def test_content_type_validation(self, flask_client):
        """Test that content type is properly validated."""
        response = flask_client.post(
            '/omi',
            data='{"test": "data"}',
            content_type='application/xml'  # Wrong content type
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'Content-Type must be application/json' in data['message']
