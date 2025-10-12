#!/usr/bin/env python3
"""
Test Utilities and Helper Functions for Thalamus Testing Suite

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
import json
import tempfile
import shutil
import sqlite3
import time
import asyncio
import subprocess
from datetime import datetime, UTC, timedelta
from typing import Dict, List, Any, Optional, Generator
from pathlib import Path
import pytest
from unittest.mock import Mock, patch
import requests
from faker import Faker

# Initialize Faker for generating test data
fake = Faker()


class TestDataGenerator:
    """Generate realistic test data for Thalamus testing."""
    
    @staticmethod
    def generate_session_data(session_id: str = None, segment_count: int = 5) -> Dict[str, Any]:
        """Generate realistic session data for testing."""
        if session_id is None:
            session_id = f"test_session_{fake.uuid4()[:8]}"
        
        segments = []
        current_time = 0.0
        
        for i in range(segment_count):
            speaker_id = fake.random_int(min=1, max=4)
            text = fake.sentence(nb_words=fake.random_int(min=5, max=15))
            duration = fake.random.uniform(1.0, 4.0)
            
            segments.append({
                "speaker_id": speaker_id,
                "text": text,
                "start_time": current_time,
                "end_time": current_time + duration
            })
            
            current_time += duration + fake.random.uniform(0.1, 1.0)
        
        return {
            "session_id": session_id,
            "log_timestamp": datetime.now(UTC).isoformat() + "Z",
            "segments": segments
        }
    
    @staticmethod
    def generate_meeting_data(duration_minutes: int = 30) -> Dict[str, Any]:
        """Generate realistic meeting data."""
        session_id = f"meeting_{fake.date_time().strftime('%Y%m%d_%H%M')}"
        segments = []
        current_time = 0.0
        speakers = ["Alice", "Bob", "Charlie", "Diana"]
        
        # Generate meeting segments
        while current_time < duration_minutes * 60:
            speaker_id = fake.random_int(min=1, max=4)
            speaker_name = speakers[speaker_id - 1]
            
            # Generate realistic meeting content
            if current_time < 60:  # First minute - introductions
                text = f"Hello everyone, I'm {speaker_name}. Thanks for joining today."
            elif current_time < 300:  # First 5 minutes - agenda
                text = f"Let's discuss the project timeline and current status."
            elif current_time < 900:  # 5-15 minutes - discussion
                text = f"I think we should focus on the core features first."
            elif current_time < 1500:  # 15-25 minutes - deep dive
                text = f"The technical implementation is more complex than expected."
            else:  # Last 5 minutes - wrap up
                text = f"Let's summarize the action items and next steps."
            
            duration = fake.random.uniform(2.0, 8.0)
            segments.append({
                "speaker_id": speaker_id,
                "text": text,
                "start_time": current_time,
                "end_time": current_time + duration
            })
            
            current_time += duration + fake.random.uniform(0.5, 2.0)
        
        return {
            "session_id": session_id,
            "log_timestamp": datetime.now(UTC).isoformat() + "Z",
            "segments": segments
        }
    
    @staticmethod
    def generate_interview_data() -> Dict[str, Any]:
        """Generate realistic interview data."""
        session_id = f"interview_{fake.uuid4()[:8]}"
        
        interview_questions = [
            "Can you tell me about your experience with Python?",
            "What frameworks have you worked with?",
            "How do you approach testing in your projects?",
            "What's your experience with database design?",
            "How do you handle performance optimization?",
            "Can you describe a challenging problem you've solved?",
            "What's your approach to code review and collaboration?",
            "How do you stay updated with new technologies?"
        ]
        
        candidate_responses = [
            "I've been working with Python for about five years, primarily in web development.",
            "I've used Django extensively, and I'm also familiar with Flask and FastAPI.",
            "I believe in comprehensive testing using pytest and maintaining high coverage.",
            "I've designed both relational and NoSQL databases for various applications.",
            "I focus on profiling first, then optimizing bottlenecks systematically.",
            "I once optimized a slow database query that was taking 30 seconds down to 200ms.",
            "I believe in constructive feedback and learning from different perspectives.",
            "I follow tech blogs, attend conferences, and contribute to open source projects."
        ]
        
        segments = []
        current_time = 0.0
        
        for i in range(len(interview_questions)):
            # Interviewer question
            segments.append({
                "speaker_id": 1,
                "text": interview_questions[i],
                "start_time": current_time,
                "end_time": current_time + 3.0
            })
            current_time += 3.5
            
            # Candidate response
            segments.append({
                "speaker_id": 2,
                "text": candidate_responses[i],
                "start_time": current_time,
                "end_time": current_time + 8.0
            })
            current_time += 8.5
        
        return {
            "session_id": session_id,
            "log_timestamp": datetime.now(UTC).isoformat() + "Z",
            "segments": segments
        }
    
    @staticmethod
    def generate_malformed_data() -> List[Dict[str, Any]]:
        """Generate various types of malformed data for error testing."""
        return [
            # Missing session_id
            {
                "segments": [{"speaker_id": 1, "text": "test", "start_time": 0.0, "end_time": 1.0}],
                "log_timestamp": datetime.now(UTC).isoformat() + "Z"
            },
            # Missing segments
            {
                "session_id": "test_session",
                "log_timestamp": datetime.now(UTC).isoformat() + "Z"
            },
            # Empty segments
            {
                "session_id": "test_session",
                "segments": [],
                "log_timestamp": datetime.now(UTC).isoformat() + "Z"
            },
            # Invalid segment structure
            {
                "session_id": "test_session",
                "segments": [{"invalid": "structure"}],
                "log_timestamp": datetime.now(UTC).isoformat() + "Z"
            },
            # Invalid timestamps
            {
                "session_id": "test_session",
                "segments": [{"speaker_id": 1, "text": "test", "start_time": "invalid", "end_time": 1.0}],
                "log_timestamp": datetime.now(UTC).isoformat() + "Z"
            }
        ]


class DatabaseTestHelper:
    """Helper functions for database testing."""
    
    @staticmethod
    def create_test_database(db_path: str) -> sqlite3.Connection:
        """Create a test database with schema."""
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Create tables
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS speakers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS raw_segments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                speaker_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                start_time REAL NOT NULL,
                end_time REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (speaker_id) REFERENCES speakers (id)
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS refined_segments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                refined_speaker_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                start_time REAL NOT NULL,
                end_time REAL NOT NULL,
                confidence_score REAL DEFAULT 0,
                source_segments TEXT,
                metadata TEXT,
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_processing INTEGER DEFAULT 0,
                FOREIGN KEY (refined_speaker_id) REFERENCES speakers (id)
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS segment_usage (
                raw_segment_id INTEGER PRIMARY KEY,
                refined_segment_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (refined_segment_id) REFERENCES refined_segments (id)
            )
        ''')
        
        conn.commit()
        return conn
    
    @staticmethod
    def populate_test_data(conn: sqlite3.Connection, session_count: int = 5) -> None:
        """Populate database with test data."""
        cur = conn.cursor()
        
        # Create sessions
        for i in range(session_count):
            cur.execute(
                "INSERT INTO sessions (session_id) VALUES (?)",
                (f"test_session_{i}",)
            )
        
        # Create speakers
        speakers = ["Alice", "Bob", "Charlie", "Diana"]
        for speaker in speakers:
            cur.execute(
                "INSERT INTO speakers (name) VALUES (?)",
                (speaker,)
            )
        
        # Create segments
        for i in range(session_count):
            session_id = i + 1
            for j in range(3):  # 3 segments per session
                speaker_id = (j % 4) + 1
                cur.execute(
                    "INSERT INTO raw_segments (session_id, speaker_id, text, start_time, end_time) VALUES (?, ?, ?, ?, ?)",
                    (session_id, speaker_id, f"Test segment {j} for session {i}", float(j), float(j + 1))
                )
        
        conn.commit()
    
    @staticmethod
    def verify_database_integrity(conn: sqlite3.Connection) -> bool:
        """Verify database integrity."""
        cur = conn.cursor()
        
        # Check foreign key constraints
        cur.execute("PRAGMA foreign_key_check")
        foreign_key_errors = cur.fetchall()
        if foreign_key_errors:
            return False
        
        # Check for orphaned records
        cur.execute("""
            SELECT COUNT(*) FROM raw_segments rs
            LEFT JOIN sessions s ON rs.session_id = s.id
            WHERE s.id IS NULL
        """)
        orphaned_segments = cur.fetchone()[0]
        if orphaned_segments > 0:
            return False
        
        return True


class PerformanceTestHelper:
    """Helper functions for performance testing."""
    
    @staticmethod
    def measure_execution_time(func, *args, **kwargs):
        """Measure execution time of a function."""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time
    
    @staticmethod
    async def measure_async_execution_time(async_func, *args, **kwargs):
        """Measure execution time of an async function."""
        start_time = time.time()
        result = await async_func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time
    
    @staticmethod
    def generate_load_test_data(request_count: int = 100) -> List[Dict[str, Any]]:
        """Generate data for load testing."""
        test_data = []
        for i in range(request_count):
            data = TestDataGenerator.generate_session_data(f"load_test_{i}", segment_count=2)
            test_data.append(data)
        return test_data
    
    @staticmethod
    def benchmark_database_operations(conn: sqlite3.Connection, operation_count: int = 1000):
        """Benchmark database operations."""
        cur = conn.cursor()
        
        # Benchmark INSERT operations
        start_time = time.time()
        for i in range(operation_count):
            cur.execute(
                "INSERT INTO sessions (session_id) VALUES (?)",
                (f"benchmark_session_{i}",)
            )
        conn.commit()
        insert_time = time.time() - start_time
        
        # Benchmark SELECT operations
        start_time = time.time()
        for i in range(operation_count):
            cur.execute("SELECT * FROM sessions WHERE session_id = ?", (f"benchmark_session_{i}",))
            cur.fetchone()
        select_time = time.time() - start_time
        
        # Benchmark UPDATE operations
        start_time = time.time()
        for i in range(operation_count):
            cur.execute(
                "UPDATE sessions SET created_at = CURRENT_TIMESTAMP WHERE session_id = ?",
                (f"benchmark_session_{i}",)
            )
        conn.commit()
        update_time = time.time() - start_time
        
        return {
            "insert_time": insert_time,
            "select_time": select_time,
            "update_time": update_time,
            "operations_per_second": {
                "insert": operation_count / insert_time,
                "select": operation_count / select_time,
                "update": operation_count / update_time
            }
        }


class MockHelper:
    """Helper functions for creating mocks."""
    
    @staticmethod
    def create_openai_mock_response(text: str = "Mock refined response") -> Mock:
        """Create a mock OpenAI API response."""
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content=text))
        ]
        mock_response.usage = Mock(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )
        return mock_response
    
    @staticmethod
    def create_openai_client_mock(responses: List[str] = None) -> Mock:
        """Create a mock OpenAI client."""
        if responses is None:
            responses = ["Mock response"]
        
        mock_client = Mock()
        mock_responses = [MockHelper.create_openai_mock_response(text) for text in responses]
        mock_client.chat.completions.create.side_effect = mock_responses
        return mock_client
    
    @staticmethod
    def create_http_response_mock(status_code: int = 200, json_data: Dict = None) -> Mock:
        """Create a mock HTTP response."""
        if json_data is None:
            json_data = {"status": "success"}
        
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.json.return_value = json_data
        return mock_response


class TestEnvironmentManager:
    """Manage test environment and cleanup."""
    
    def __init__(self):
        self.temp_dirs = []
        self.temp_files = []
        self.processes = []
    
    def create_temp_dir(self, prefix: str = "thalamus_test_") -> str:
        """Create a temporary directory."""
        temp_dir = tempfile.mkdtemp(prefix=prefix)
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    def create_temp_file(self, content: str = "", suffix: str = ".tmp") -> str:
        """Create a temporary file."""
        fd, temp_file = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        self.temp_files.append(temp_file)
        return temp_file
    
    def start_process(self, command: List[str], cwd: str = None) -> subprocess.Popen:
        """Start a subprocess."""
        process = subprocess.Popen(command, cwd=cwd)
        self.processes.append(process)
        return process
    
    def cleanup(self):
        """Clean up all temporary resources."""
        # Stop processes
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except (subprocess.TimeoutExpired, ProcessLookupError):
                try:
                    process.kill()
                except ProcessLookupError:
                    pass
        
        # Remove temporary files
        for temp_file in self.temp_files:
            try:
                os.unlink(temp_file)
            except OSError:
                pass
        
        # Remove temporary directories
        for temp_dir in self.temp_dirs:
            try:
                shutil.rmtree(temp_dir)
            except OSError:
                pass


class AsyncTestHelper:
    """Helper functions for async testing."""
    
    @staticmethod
    async def run_concurrent_tasks(tasks: List[callable], max_concurrent: int = 10):
        """Run tasks concurrently with a limit."""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def run_with_semaphore(task):
            async with semaphore:
                return await task()
        
        return await asyncio.gather(*[run_with_semaphore(task) for task in tasks])
    
    @staticmethod
    async def wait_for_condition(condition_func, timeout: float = 10.0, interval: float = 0.1):
        """Wait for a condition to become true."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if condition_func():
                return True
            await asyncio.sleep(interval)
        return False
    
    @staticmethod
    async def simulate_async_processing(data: List[Any], processing_func: callable, delay: float = 0.1):
        """Simulate async processing with delays."""
        results = []
        for item in data:
            await asyncio.sleep(delay)
            result = await processing_func(item)
            results.append(result)
        return results


# Pytest fixtures using the helper classes
@pytest.fixture
def test_data_generator():
    """Provide test data generator."""
    return TestDataGenerator()


@pytest.fixture
def database_helper():
    """Provide database helper."""
    return DatabaseTestHelper()


@pytest.fixture
def performance_helper():
    """Provide performance helper."""
    return PerformanceTestHelper()


@pytest.fixture
def mock_helper():
    """Provide mock helper."""
    return MockHelper()


@pytest.fixture
def test_env_manager():
    """Provide test environment manager."""
    manager = TestEnvironmentManager()
    yield manager
    manager.cleanup()


@pytest.fixture
def async_helper():
    """Provide async helper."""
    return AsyncTestHelper()


# Utility functions for common test patterns
def assert_response_success(response, expected_status: int = 200):
    """Assert that a response indicates success."""
    assert response.status_code == expected_status
    if hasattr(response, 'get_json'):
        data = response.get_json()
        assert data.get('status') == 'success'


def assert_response_error(response, expected_status: int = 400):
    """Assert that a response indicates an error."""
    assert response.status_code == expected_status
    if hasattr(response, 'get_json'):
        data = response.get_json()
        assert data.get('status') == 'error'


def assert_database_contains(conn: sqlite3.Connection, table: str, **conditions):
    """Assert that database contains records matching conditions."""
    cur = conn.cursor()
    
    where_clause = " AND ".join([f"{key} = ?" for key in conditions.keys()])
    query = f"SELECT COUNT(*) FROM {table}"
    if where_clause:
        query += f" WHERE {where_clause}"
    
    cur.execute(query, list(conditions.values()))
    count = cur.fetchone()[0]
    assert count > 0, f"No records found in {table} matching {conditions}"


def assert_database_empty(conn: sqlite3.Connection, table: str):
    """Assert that a database table is empty."""
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    count = cur.fetchone()[0]
    assert count == 0, f"Table {table} is not empty, contains {count} records"
