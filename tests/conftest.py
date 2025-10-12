#!/usr/bin/env python3
"""
Pytest Configuration and Shared Fixtures for Thalamus Testing Suite

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

import os
import sys
import tempfile
import shutil
import pytest
import asyncio
from pathlib import Path
from typing import Generator, Dict, Any
from unittest.mock import Mock, patch
import sqlite3
from datetime import datetime, UTC

# Add the examples directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "examples"))

# Import Thalamus modules
from thalamus_system.core.database import init_db, get_db, DB_PATH
from thalamus_system.core.logging_config import setup_logging, get_logger
from thalamus_system.core.response_utils import create_success_response, create_error_response


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_logger():
    """Set up logging for tests."""
    # Configure logging for tests
    os.environ['LOG_LEVEL'] = 'DEBUG'
    os.environ['LOG_FORMAT'] = 'text'
    setup_logging()
    return get_logger('test')


@pytest.fixture(scope="function")
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp(prefix="thalamus_test_")
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture(scope="function")
def temp_db_path(temp_dir):
    """Create a temporary database path for testing."""
    return os.path.join(temp_dir, "test_thalamus.db")


@pytest.fixture(scope="function")
def test_db(temp_db_path):
    """Create a test database with schema."""
    # Set environment to use test database
    original_db_path = DB_PATH
    os.environ['THALAMUS_DB_PATH'] = temp_db_path
    os.environ['ENVIRONMENT'] = 'test'
    
    # Initialize the test database
    init_db()
    
    yield temp_db_path
    
    # Cleanup
    if os.path.exists(temp_db_path):
        os.remove(temp_db_path)
    os.environ.pop('THALAMUS_DB_PATH', None)
    os.environ.pop('ENVIRONMENT', None)


@pytest.fixture(scope="function")
def db_connection(test_db):
    """Get a database connection for testing."""
    with get_db() as conn:
        yield conn


@pytest.fixture(scope="function")
def sample_session_data():
    """Sample session data for testing."""
    return {
        "session_id": "test_session_123",
        "log_timestamp": datetime.now(UTC).isoformat() + "Z",
        "segments": [
            {
                "speaker_id": 1,
                "text": "Hello, this is a test segment.",
                "start_time": 0.0,
                "end_time": 2.5
            },
            {
                "speaker_id": 2,
                "text": "This is another test segment.",
                "start_time": 2.5,
                "end_time": 5.0
            }
        ]
    }


@pytest.fixture(scope="function")
def sample_speakers():
    """Sample speaker data for testing."""
    return [
        {"id": 1, "name": "Speaker One", "is_user": True},
        {"id": 2, "name": "Speaker Two", "is_user": False},
        {"id": 3, "name": "Speaker Three", "is_user": False}
    ]


@pytest.fixture(scope="function")
def mock_openai_response():
    """Mock OpenAI API response for testing."""
    return {
        "choices": [
            {
                "message": {
                    "content": "This is a refined transcript with improved grammar and clarity."
                }
            }
        ],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150
        }
    }


@pytest.fixture(scope="function")
def mock_openai_client(mock_openai_response):
    """Mock OpenAI client for testing."""
    mock_client = Mock()
    mock_client.chat.completions.create.return_value = Mock()
    mock_client.chat.completions.create.return_value.choices = [
        Mock(message=Mock(content=mock_openai_response["choices"][0]["message"]["content"]))
    ]
    mock_client.chat.completions.create.return_value.usage = Mock(
        prompt_tokens=mock_openai_response["usage"]["prompt_tokens"],
        completion_tokens=mock_openai_response["usage"]["completion_tokens"],
        total_tokens=mock_openai_response["usage"]["total_tokens"]
    )
    return mock_client


@pytest.fixture(scope="function")
def flask_app():
    """Create a Flask app instance for testing."""
    from thalamus_system.webhook_server.omi_webhook import app
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app


@pytest.fixture(scope="function")
def flask_client(flask_app):
    """Create a Flask test client."""
    return flask_app.test_client()


@pytest.fixture(scope="function")
def mock_requests():
    """Mock requests library for HTTP testing."""
    with patch('requests.post') as mock_post, \
         patch('requests.get') as mock_get, \
         patch('requests.put') as mock_put, \
         patch('requests.delete') as mock_delete:
        
        # Set up default responses
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"status": "success"}
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"data": "test"}
        mock_put.return_value.status_code = 200
        mock_put.return_value.json.return_value = {"status": "updated"}
        mock_delete.return_value.status_code = 200
        mock_delete.return_value.json.return_value = {"status": "deleted"}
        
        yield {
            'post': mock_post,
            'get': mock_get,
            'put': mock_put,
            'delete': mock_delete
        }


@pytest.fixture(scope="function")
def mock_env_vars():
    """Mock environment variables for testing."""
    env_vars = {
        'OPENAI_API_KEY': 'test-api-key-12345',
        'THALAMUS_DB_PATH': ':memory:',
        'ENVIRONMENT': 'test',
        'LOG_LEVEL': 'DEBUG',
        'LOG_FORMAT': 'text',
        'MAX_REQUEST_SIZE_MB': '10',
        'MAX_JSON_SIZE_MB': '5'
    }
    
    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture(scope="function")
def freeze_time():
    """Freeze time for testing datetime-dependent code."""
    from freezegun import freeze_time
    frozen_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
    with freeze_time(frozen_time):
        yield frozen_time


@pytest.fixture(scope="function")
def performance_timer():
    """Timer fixture for performance testing."""
    import time
    start_time = time.time()
    yield start_time
    end_time = time.time()
    print(f"\nTest execution time: {end_time - start_time:.4f} seconds")


# Async test fixtures
@pytest.fixture(scope="function")
async def async_db_connection(test_db):
    """Get an async database connection for testing."""
    # For now, we'll use the sync connection wrapped in asyncio
    # In the future, this could be replaced with an async database driver
    loop = asyncio.get_event_loop()
    with get_db() as conn:
        yield conn


@pytest.fixture(scope="function")
async def async_mock_openai():
    """Async mock for OpenAI API calls."""
    async def mock_openai_call(*args, **kwargs):
        return {
            "choices": [{"message": {"content": "Async mock response"}}],
            "usage": {"total_tokens": 100}
        }
    return mock_openai_call


# Test data factories
@pytest.fixture(scope="function")
def segment_factory():
    """Factory for creating test segments."""
    def create_segment(speaker_id=1, text="Test segment", start_time=0.0, end_time=1.0):
        return {
            "speaker_id": speaker_id,
            "text": text,
            "start_time": start_time,
            "end_time": end_time
        }
    return create_segment


@pytest.fixture(scope="function")
def session_factory():
    """Factory for creating test sessions."""
    def create_session(session_id="test_session", segment_count=3):
        segments = []
        for i in range(segment_count):
            segments.append({
                "speaker_id": (i % 3) + 1,
                "text": f"Test segment {i+1}",
                "start_time": float(i * 2),
                "end_time": float((i + 1) * 2)
            })
        
        return {
            "session_id": session_id,
            "log_timestamp": datetime.now(UTC).isoformat() + "Z",
            "segments": segments
        }
    return create_session


# Cleanup fixtures
@pytest.fixture(scope="function", autouse=True)
def cleanup_test_files():
    """Automatically clean up test files after each test."""
    yield
    # Clean up any test files that might have been created
    test_files = [
        "test_thalamus.db",
        "test.log",
        "test_output.json"
    ]
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)


# Test markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests - fast, isolated tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests - test component interactions"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests - full system tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests that take more than 5 seconds"
    )
    config.addinivalue_line(
        "markers", "async: Async tests requiring special handling"
    )
    config.addinivalue_line(
        "markers", "database: Tests that require database access"
    )
    config.addinivalue_line(
        "markers", "api: API endpoint tests"
    )
    config.addinivalue_line(
        "markers", "performance: Performance and load tests"
    )
    config.addinivalue_line(
        "markers", "security: Security-related tests"
    )
    config.addinivalue_line(
        "markers", "smoke: Smoke tests for basic functionality"
    )


# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        
        # Add database marker if test uses database fixtures
        if "db_" in item.name or "database" in item.name:
            item.add_marker(pytest.mark.database)
        
        # Add async marker if test is async
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)
