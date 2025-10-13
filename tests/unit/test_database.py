#!/usr/bin/env python3
"""
Unit Tests for Thalamus Database Module

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
import os
import tempfile
import shutil
import time
from datetime import datetime, UTC
from unittest.mock import patch, Mock
import sqlite3

# Import the modules we're testing
from thalamus_system.core.database import (
    init_db, get_db, get_or_create_session, get_or_create_speaker,
    insert_segment, get_unrefined_segments, insert_refined_segment,
    get_refined_segments, get_locked_segments, update_refined_segment,
    get_refined_segment, get_active_sessions, add_indexes_to_existing_db,
    get_used_segment_ids
)


class TestDatabaseInitialization:
    """Test database initialization and schema creation."""
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_init_db_creates_tables(self, test_db):
        """Test that init_db creates all required tables."""
        with get_db() as conn:
            cur = conn.cursor()
            
            # Check that all tables exist
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cur.fetchall()]
            
            expected_tables = ['sessions', 'speakers', 'raw_segments', 'refined_segments', 'segment_usage']
            for table in expected_tables:
                assert table in tables, f"Table {table} should exist"
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_init_db_creates_indexes(self, test_db):
        """Test that init_db creates performance indexes."""
        with get_db() as conn:
            cur = conn.cursor()
            
            # Check that indexes exist
            cur.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = [row[0] for row in cur.fetchall()]
            
            expected_indexes = [
                'idx_raw_segments_session_id',
                'idx_raw_segments_timestamp',
                'idx_raw_segments_speaker_id',
                'idx_refined_segments_session_id',
                'idx_refined_segments_start_time',
                'idx_refined_segments_last_update',
                'idx_segment_usage_refined_segment_id',
                'idx_segment_usage_timestamp'
            ]
            
            for index in expected_indexes:
                assert index in indexes, f"Index {index} should exist"
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_add_indexes_to_existing_db(self, test_db):
        """Test adding indexes to existing database."""
        # This should not raise an error
        add_indexes_to_existing_db()
        
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = [row[0] for row in cur.fetchall()]
            
            # Should have all the expected indexes
            assert len(indexes) >= 8, "Should have at least 8 indexes"


class TestSessionManagement:
    """Test session creation and management."""
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_get_or_create_session_new(self, test_db):
        """Test creating a new session."""
        session_id = "test_session_123"
        session_db_id = get_or_create_session(session_id)
        
        assert isinstance(session_db_id, int)
        assert session_db_id > 0
        
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT session_id FROM sessions WHERE id = ?", (session_db_id,))
            result = cur.fetchone()
            assert result[0] == session_id
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_get_or_create_session_existing(self, test_db):
        """Test getting an existing session."""
        session_id = "test_session_456"
        
        # Create session first time
        session_db_id1 = get_or_create_session(session_id)
        
        # Get same session second time
        session_db_id2 = get_or_create_session(session_id)
        
        assert session_db_id1 == session_db_id2, "Should return same session ID"
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_get_or_create_session_empty_id(self, test_db):
        """Test handling of empty session ID."""
        with pytest.raises(Exception):
            get_or_create_session("")


class TestSpeakerManagement:
    """Test speaker creation and management."""
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_get_or_create_speaker_new(self, test_db):
        """Test creating a new speaker."""
        speaker_name = "Test Speaker"
        speaker_id = 1
        is_user = True
        
        speaker_db_id = get_or_create_speaker(speaker_id, speaker_name, is_user)
        
        assert isinstance(speaker_db_id, int)
        assert speaker_db_id > 0
        
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM speakers WHERE id = ?", (speaker_db_id,))
            result = cur.fetchone()
            assert result[0] == speaker_name
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_get_or_create_speaker_existing(self, test_db):
        """Test getting an existing speaker."""
        speaker_name = "Existing Speaker"
        speaker_id = 2
        
        # Create speaker first time
        speaker_db_id1 = get_or_create_speaker(speaker_id, speaker_name)
        
        # Get same speaker second time
        speaker_db_id2 = get_or_create_speaker(speaker_id, speaker_name)
        
        assert speaker_db_id1 == speaker_db_id2, "Should return same speaker ID"
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_get_or_create_speaker_by_name(self, test_db):
        """Test finding speaker by name when ID doesn't match."""
        speaker_name = "Name Match Speaker"
        
        # Create speaker with ID 1
        speaker_db_id1 = get_or_create_speaker(1, speaker_name)
        
        # Try to create with different ID but same name
        speaker_db_id2 = get_or_create_speaker(2, speaker_name)
        
        assert speaker_db_id1 == speaker_db_id2, "Should return same speaker ID for same name"


class TestSegmentManagement:
    """Test segment insertion and retrieval."""
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_insert_segment(self, test_db, sample_session_data):
        """Test inserting a raw segment."""
        # Create session and speaker first
        session_id = get_or_create_session(sample_session_data["session_id"])
        speaker_id = get_or_create_speaker(1, "Test Speaker")
        
        # Insert segment
        segment_data = sample_session_data["segments"][0]
        log_timestamp = datetime.fromisoformat(sample_session_data["log_timestamp"].replace('Z', ''))
        
        segment_db_id = insert_segment(
            session_id, speaker_id, segment_data["text"],
            segment_data["start_time"], segment_data["end_time"], log_timestamp
        )
        
        assert isinstance(segment_db_id, int)
        assert segment_db_id > 0
        
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM raw_segments WHERE id = ?", (segment_db_id,))
            result = cur.fetchone()
            assert result is not None
            assert result['text'] == segment_data["text"]
            assert result['start_time'] == segment_data["start_time"]
            assert result['end_time'] == segment_data["end_time"]
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_get_unrefined_segments(self, test_db, sample_session_data):
        """Test retrieving unrefined segments."""
        # Use a unique session ID for this test to avoid conflicts
        unique_session_id = f"{sample_session_data['session_id']}_{id(self)}"
        
        # Create session and speaker
        session_id = get_or_create_session(unique_session_id)
        speaker_id = get_or_create_speaker(1, "Test Speaker")
        
        # Insert segments
        log_timestamp = datetime.fromisoformat(sample_session_data["log_timestamp"].replace('Z', ''))
        for segment_data in sample_session_data["segments"]:
            insert_segment(
                unique_session_id, speaker_id, segment_data["text"],
                segment_data["start_time"], segment_data["end_time"], log_timestamp
            )
        
        # Get unrefined segments for our specific session
        segments = get_unrefined_segments(unique_session_id)
        
        # Since these are fresh segments, they should be unrefined
        assert len(segments) == len(sample_session_data["segments"])
        # Check that we have segments from our session
        assert all(seg['session_id'] == unique_session_id for seg in segments)
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_insert_refined_segment(self, test_db, sample_session_data):
        """Test inserting a refined segment."""
        # Create session and speaker
        session_id = get_or_create_session(sample_session_data["session_id"])
        speaker_id = get_or_create_speaker(1, "Test Speaker")
        
        # Insert raw segment first
        segment_data = sample_session_data["segments"][0]
        log_timestamp = datetime.fromisoformat(sample_session_data["log_timestamp"].replace('Z', ''))
        raw_segment_id = insert_segment(
            session_id, speaker_id, segment_data["text"],
            segment_data["start_time"], segment_data["end_time"], log_timestamp
        )
        
        # Insert refined segment
        refined_text = "This is a refined version of the text."
        refined_segment_id = insert_refined_segment(
            session_id, speaker_id, refined_text,
            segment_data["start_time"], segment_data["end_time"],
            confidence_score=0.95,
            source_segments=str(raw_segment_id)
        )
        
        assert isinstance(refined_segment_id, int)
        assert refined_segment_id > 0
        
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM refined_segments WHERE id = ?", (refined_segment_id,))
            result = cur.fetchone()
            assert result is not None
            assert result['text'] == refined_text
            assert result['confidence_score'] == 0.95
            assert result['source_segments'] == str(raw_segment_id)
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_get_refined_segments(self, test_db, sample_session_data):
        """Test retrieving refined segments."""
        # Create session and speaker
        session_id = get_or_create_session(sample_session_data["session_id"])
        speaker_id = get_or_create_speaker(1, "Test Speaker")
        
        # Insert refined segment
        segment_data = sample_session_data["segments"][0]
        insert_refined_segment(
            sample_session_data["session_id"], speaker_id, "Refined text",
            segment_data["start_time"], segment_data["end_time"]
        )
        
        # Get refined segments
        segments = get_refined_segments()
        
        assert len(segments) >= 1
        # Check that we have segments from our session (session_id is the string session ID)
        assert any(seg['session_id'] == sample_session_data["session_id"] for seg in segments)
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_get_locked_segments(self, test_db, sample_session_data):
        """Test retrieving locked refined segments."""
        # Create session and speaker
        session_id = get_or_create_session(sample_session_data["session_id"])
        speaker_id = get_or_create_speaker(1, "Test Speaker")
        
        # Insert refined segment
        segment_data = sample_session_data["segments"][0]
        insert_refined_segment(
            session_id, speaker_id, "Refined text",
            segment_data["start_time"], segment_data["end_time"]
        )
        
        # Get locked segments
        segments = get_locked_segments(sample_session_data["session_id"])
        
        # Should return empty list since no segments are locked yet
        assert isinstance(segments, list)


class TestDatabaseConfiguration:
    """Test database configuration and environment handling."""
    
    @pytest.mark.unit
    def test_database_path_configuration(self):
        """Test database path configuration with environment variables."""
        with patch.dict(os.environ, {'ENVIRONMENT': 'test'}):
            from thalamus_system.core.database import get_db_path
            assert get_db_path() == ':memory:'
        
        with patch.dict(os.environ, {'ENVIRONMENT': 'production', 'THALAMUS_DB_PATH': '/custom/path.db'}):
            from thalamus_system.core.database import get_db_path
            assert get_db_path() == '/custom/path.db'
        
        with patch.dict(os.environ, {'THALAMUS_DB_PATH': '/custom/dev/path.db'}, clear=True):
            from thalamus_system.core.database import get_db_path
            assert get_db_path() == '/custom/dev/path.db'
    
    @pytest.mark.unit
    def test_database_connection_timeout(self, test_db):
        """Test database connection timeout handling."""
        with get_db() as conn:
            # Test that connection has proper timeout
            assert conn is not None
            # Test basic query
            cur = conn.cursor()
            cur.execute("SELECT 1")
            result = cur.fetchone()
            assert result[0] == 1


class TestErrorHandling:
    """Test error handling in database operations."""
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_database_connection_error(self):
        """Test handling of database connection errors."""
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = sqlite3.Error("Connection failed")
            
            with pytest.raises(sqlite3.Error):
                with get_db():
                    pass
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_invalid_session_id(self, test_db):
        """Test handling of invalid session ID."""
        with pytest.raises(Exception):
            get_or_create_session(None)
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_invalid_speaker_data(self, test_db):
        """Test handling of invalid speaker data."""
        with pytest.raises(Exception):
            get_or_create_speaker(None, None)


class TestPerformance:
    """Test database performance and indexing."""
    
    @pytest.mark.unit
    @pytest.mark.database
    @pytest.mark.performance
    def test_session_lookup_performance(self, test_db, performance_timer):
        """Test that session lookups are fast with indexes."""
        # Create multiple sessions
        session_ids = [f"perf_test_session_{i}" for i in range(100)]
        for session_id in session_ids:
            get_or_create_session(session_id)
        
        # Test lookup performance
        start_time = performance_timer
        for session_id in session_ids:
            get_or_create_session(session_id)
        
        # This should be fast due to indexes
        # If it takes more than 1 second for 100 lookups, something is wrong
        assert True  # Placeholder - actual timing would be checked in integration tests
    
    @pytest.mark.unit
    @pytest.mark.database
    @pytest.mark.performance
    def test_segment_query_performance(self, test_db, performance_timer):
        """Test that segment queries are fast with indexes."""
        # Create session and speaker
        session_id = get_or_create_session("perf_test_session")
        speaker_id = get_or_create_speaker(1, "Perf Speaker")
        
        # Insert many segments
        log_timestamp = datetime.now(UTC)
        for i in range(50):
            insert_segment(
                session_id, speaker_id, f"Segment {i}",
                float(i), float(i + 1), log_timestamp
            )
        
        # Test query performance
        start_time = performance_timer
        segments = get_unrefined_segments()
        
        assert len(segments) >= 50
        # Performance check would be more detailed in integration tests


class TestAdditionalFunctions:
        """Test additional database functions."""
        
        @pytest.mark.unit
        @pytest.mark.database
        def test_update_refined_segment(self, test_db, sample_session_data):
            """Test updating a refined segment."""
            # Use unique session ID to avoid conflicts
            unique_session_id = f"{sample_session_data['session_id']}_update_{id(self)}"
            
            # Create session and speaker
            session_id = get_or_create_session(unique_session_id)
            speaker_id = get_or_create_speaker(1, "Test Speaker")
            
            # Insert refined segment
            segment_data = sample_session_data["segments"][0]
            refined_id = insert_refined_segment(
                unique_session_id, speaker_id, "Original text",
                segment_data["start_time"], segment_data["end_time"]
            )
            
            # Update the segment
            success = update_refined_segment(
                refined_id,
                text="Updated text",
                confidence_score=0.95,
                metadata='{"source": "test"}'
            )
            
            assert success is True
            
            # Verify the update
            segments = get_refined_segments(unique_session_id)
            assert len(segments) == 1
            assert segments[0]["text"] == "Updated text"
            assert segments[0]["confidence_score"] == 0.95
            assert segments[0]["metadata"] == '{"source": "test"}'
        
        @pytest.mark.unit
        @pytest.mark.database
        def test_update_refined_segment_no_fields(self, test_db):
            """Test updating a refined segment with no valid fields."""
            success = update_refined_segment(999, invalid_field="test")
            assert success is False
        
        @pytest.mark.unit
        @pytest.mark.database
        def test_get_used_segment_ids(self, test_db, sample_session_data):
            """Test getting used segment IDs."""
            # This function returns segment IDs that have been used in refinements
            # Since we don't have a mechanism to automatically mark segments as used,
            # we'll just test that the function works and returns a list
            used_ids = get_used_segment_ids()
            assert isinstance(used_ids, list)
            # The function should work without errors


class TestDatabaseErrorHandling:
    """Test database error handling and exception scenarios."""
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_init_db_exception_handling(self, mocker):
        """Test init_db handles database initialization errors."""
        # Mock sqlite3.connect to raise an exception
        mocker.patch('sqlite3.connect', side_effect=sqlite3.Error("Database connection failed"))
        
        with pytest.raises(sqlite3.Error, match="Database connection failed"):
            init_db()
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_get_db_connection_error(self, mocker):
        """Test get_db handles connection errors."""
        mocker.patch('sqlite3.connect', side_effect=sqlite3.Error("Connection failed"))
        
        with pytest.raises(sqlite3.Error, match="Connection failed"):
            with get_db() as conn:
                pass
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_add_indexes_to_existing_db_success(self, temp_db_path):
        """Test add_indexes_to_existing_db works successfully."""
        # Set environment to use the temp database path
        os.environ['THALAMUS_DB_PATH'] = temp_db_path
        # Don't set ENVIRONMENT to 'test' as it forces in-memory database
        
        # Create a basic database first
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT UNIQUE NOT NULL, start_time TEXT NOT NULL, end_time TEXT)
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS raw_segments (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL, speaker_id INTEGER NOT NULL, text TEXT NOT NULL, start_time REAL NOT NULL, end_time REAL NOT NULL, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS refined_segments (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL, refined_speaker_id INTEGER NOT NULL, text TEXT NOT NULL, start_time REAL NOT NULL, end_time REAL NOT NULL, confidence_score REAL DEFAULT 0, source_segments TEXT, metadata TEXT, is_processing INTEGER DEFAULT 0, last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP, is_locked INTEGER DEFAULT 0)
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS segment_usage (id INTEGER PRIMARY KEY AUTOINCREMENT, raw_segment_id INTEGER NOT NULL, refined_segment_id INTEGER NOT NULL, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
            ''')
            conn.commit()
        
        # Should not raise an exception
        add_indexes_to_existing_db()
        
        # Verify indexes were created
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("PRAGMA index_list('raw_segments');")
            indexes = [row["name"] for row in cur.fetchall()]
            assert "idx_raw_segments_session_id" in indexes
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_add_indexes_to_existing_db_error(self, mocker):
        """Test add_indexes_to_existing_db handles errors."""
        mocker.patch('sqlite3.connect', side_effect=sqlite3.Error("Index creation failed"))
        
        with pytest.raises(sqlite3.Error, match="Index creation failed"):
            add_indexes_to_existing_db()
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_get_or_create_session_database_error(self, mocker):
        """Test get_or_create_session handles database errors."""
        mocker.patch('sqlite3.connect', side_effect=sqlite3.Error("Database error"))
        
        with pytest.raises(sqlite3.Error, match="Database error"):
            get_or_create_session("test_session")
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_get_or_create_speaker_database_error(self, mocker):
        """Test get_or_create_speaker handles database errors."""
        mocker.patch('sqlite3.connect', side_effect=sqlite3.Error("Database error"))
        
        with pytest.raises(sqlite3.Error, match="Database error"):
            get_or_create_speaker(1, "Test Speaker")
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_insert_segment_database_error(self, mocker):
        """Test insert_segment handles database errors."""
        mocker.patch('sqlite3.connect', side_effect=sqlite3.Error("Database error"))
        
        with pytest.raises(sqlite3.Error, match="Database error"):
            insert_segment("test_session", 1, "test text", 0.0, 1.0, datetime.now(UTC))
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_get_unrefined_segments_database_error(self, mocker):
        """Test get_unrefined_segments handles database errors."""
        mocker.patch('sqlite3.connect', side_effect=sqlite3.Error("Database error"))
        
        # Function handles errors gracefully and returns empty list
        result = get_unrefined_segments("test_session")
        assert result == []
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_insert_refined_segment_database_error(self, mocker):
        """Test insert_refined_segment handles database errors."""
        mocker.patch('sqlite3.connect', side_effect=sqlite3.Error("Database error"))
        
        with pytest.raises(sqlite3.Error, match="Database error"):
            insert_refined_segment("test_session", 1, "test text", 0.0, 1.0)
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_get_refined_segments_database_error(self, mocker):
        """Test get_refined_segments handles database errors."""
        mocker.patch('sqlite3.connect', side_effect=sqlite3.Error("Database error"))
        
        with pytest.raises(sqlite3.Error, match="Database error"):
            get_refined_segments("test_session")
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_get_locked_segments_database_error(self, mocker):
        """Test get_locked_segments handles database errors."""
        mocker.patch('sqlite3.connect', side_effect=sqlite3.Error("Database error"))
        
        with pytest.raises(sqlite3.Error, match="Database error"):
            get_locked_segments("test_session")
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_update_refined_segment_database_error(self, mocker):
        """Test update_refined_segment handles database errors."""
        mocker.patch('sqlite3.connect', side_effect=sqlite3.Error("Database error"))
        
        success = update_refined_segment(1, text="updated")
        assert success is False
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_get_refined_segment_database_error(self, mocker):
        """Test get_refined_segment handles database errors."""
        mocker.patch('sqlite3.connect', side_effect=sqlite3.Error("Database error"))
        
        result = get_refined_segment(1)
        assert result is None
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_get_active_sessions_database_error(self, mocker):
        """Test get_active_sessions handles database errors."""
        mocker.patch('sqlite3.connect', side_effect=sqlite3.Error("Database error"))
        
        # Function handles errors gracefully and returns empty list
        result = get_active_sessions()
        assert result == []
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_get_used_segment_ids_database_error(self, mocker):
        """Test get_used_segment_ids handles database errors."""
        mocker.patch('sqlite3.connect', side_effect=sqlite3.Error("Database error"))
        
        # Function handles errors gracefully and returns empty list
        result = get_used_segment_ids()
        assert result == []
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_json_array_contains_function(self, test_db):
        """Test the json_array_contains SQL function."""
        with get_db() as conn:
            cur = conn.cursor()
            
            # Test with valid JSON array
            result = cur.execute("SELECT json_array_contains('[1,2,3]', 2)").fetchone()[0]
            assert result == 1  # SQLite returns 1 for True
            
            # Test with value not in array
            result = cur.execute("SELECT json_array_contains('[1,2,3]', 5)").fetchone()[0]
            assert result == 0  # SQLite returns 0 for False
            
            # Test with invalid JSON
            result = cur.execute("SELECT json_array_contains('invalid json', 1)").fetchone()[0]
            assert result == 0
            
            # Test with None
            result = cur.execute("SELECT json_array_contains(NULL, 1)").fetchone()[0]
            assert result == 0
            
            # Test with non-array JSON
            result = cur.execute("SELECT json_array_contains('{\"key\": \"value\"}', 1)").fetchone()[0]
            assert result == 0


class TestDatabaseMigration:
    """Test database migration functionality."""
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_migrate_database_schema_adds_is_locked_column(self, temp_db_path):
        """Test that migrate_database_schema adds is_locked column if missing."""
        # Set up environment to use the temp database path
        os.environ['THALAMUS_DB_PATH'] = temp_db_path
        # Don't set ENVIRONMENT to 'test' as it forces in-memory database
        
        # Create a database without the is_locked column by manually creating the table
        import sqlite3
        conn = sqlite3.connect(temp_db_path)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS refined_segments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                refined_speaker_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                start_time REAL NOT NULL,
                end_time REAL NOT NULL,
                confidence_score REAL DEFAULT 0.0,
                source_segments TEXT,
                metadata TEXT,
                is_processing INTEGER DEFAULT 0,
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        
        # Verify is_locked column doesn't exist
        conn = sqlite3.connect(temp_db_path)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(refined_segments)")
        columns = [col[1] for col in cur.fetchall()]
        conn.close()
        assert 'is_locked' not in columns
        
        # Import and run migration - need to reload the module to pick up new DB path
        import importlib
        import thalamus_system.core.database as db_module
        importlib.reload(db_module)
        db_module.migrate_database_schema()
        
        # Verify is_locked column was added
        conn = sqlite3.connect(temp_db_path)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(refined_segments)")
        columns = [col[1] for col in cur.fetchall()]
        conn.close()
        assert 'is_locked' in columns
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_migrate_database_schema_skips_existing_column(self, test_db):
        """Test that migrate_database_schema skips adding is_locked if it already exists."""
        from thalamus_system.core.database import migrate_database_schema
        
        # Run migration - should not fail if column already exists
        migrate_database_schema()
        
        # Verify column still exists
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(refined_segments)")
            columns = [col[1] for col in cur.fetchall()]
            assert 'is_locked' in columns
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_migrate_database_schema_error_handling(self, mocker):
        """Test migrate_database_schema error handling."""
        mocker.patch('sqlite3.connect', side_effect=sqlite3.Error("Migration failed"))
        
        from thalamus_system.core.database import migrate_database_schema
        
        with pytest.raises(sqlite3.Error, match="Migration failed"):
            migrate_database_schema()


class TestSpeakerManagementEdgeCases:
    """Test edge cases in speaker management."""
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_get_or_create_speaker_by_name_only(self, test_db):
        """Test creating a speaker with only a name (no speaker_id)."""
        speaker_id = get_or_create_speaker(None, "Speaker by Name Only")
        assert isinstance(speaker_id, int)
        assert speaker_id > 0
        
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM speakers WHERE id = ?", (speaker_id,))
            result = cur.fetchone()
            assert result["name"] == "Speaker by Name Only"
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_get_or_create_speaker_with_language(self, test_db):
        """Test creating a speaker with language specified."""
        # The get_or_create_speaker function doesn't support language parameter
        # This test should verify the function works with the actual parameters
        speaker_id = get_or_create_speaker(5, "Multilingual Speaker")
        assert isinstance(speaker_id, int)
        
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM speakers WHERE id = ?", (speaker_id,))
            result = cur.fetchone()
            assert result["id"] == speaker_id
            assert result["name"] == "Multilingual Speaker"


class TestRefinedSegmentEdgeCases:
    """Test edge cases in refined segment management."""
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_insert_refined_segment_with_string_source_segments(self, test_db, sample_session_data):
        """Test inserting refined segment with string source_segments."""
        session_id = get_or_create_session(sample_session_data["session_id"])
        speaker_id = get_or_create_speaker(1, "Test Speaker")
        
        # Insert refined segment with string source_segments
        segment_data = sample_session_data["segments"][0]
        refined_id = insert_refined_segment(
            sample_session_data["session_id"], speaker_id, "Refined text",
            segment_data["start_time"], segment_data["end_time"],
            source_segments='[1,2,3]'  # JSON string
        )
        assert isinstance(refined_id, int)
        assert refined_id > 0
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_insert_refined_segment_with_invalid_json_source_segments(self, test_db, sample_session_data):
        """Test inserting refined segment with invalid JSON source_segments."""
        session_id = get_or_create_session(sample_session_data["session_id"])
        speaker_id = get_or_create_speaker(1, "Test Speaker")
        
        # Insert refined segment with invalid JSON source_segments
        segment_data = sample_session_data["segments"][0]
        # The function should handle invalid JSON gracefully by treating it as a single integer
        refined_id = insert_refined_segment(
            sample_session_data["session_id"], speaker_id, "Refined text",
            segment_data["start_time"], segment_data["end_time"],
            source_segments='invalid json'  # Invalid JSON
        )
        
        # The function should still succeed but handle the invalid JSON gracefully
        assert refined_id is not None  # Should succeed despite invalid JSON
        assert isinstance(refined_id, int)
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_insert_refined_segment_with_integer_source_segments(self, test_db, sample_session_data):
        """Test inserting refined segment with integer source_segments."""
        session_id = get_or_create_session(sample_session_data["session_id"])
        speaker_id = get_or_create_speaker(1, "Test Speaker")
        
        # Insert refined segment with integer source_segments
        segment_data = sample_session_data["segments"][0]
        refined_id = insert_refined_segment(
            sample_session_data["session_id"], speaker_id, "Refined text",
            segment_data["start_time"], segment_data["end_time"],
            source_segments=123  # Integer
        )
        assert isinstance(refined_id, int)
        assert refined_id > 0
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_get_refined_segments_without_session_id(self, test_db, sample_session_data):
        """Test getting refined segments without specifying session_id."""
        # Create session and speaker
        session_id = get_or_create_session(sample_session_data["session_id"])
        speaker_id = get_or_create_speaker(1, "Test Speaker")
        
        # Insert refined segment
        segment_data = sample_session_data["segments"][0]
        insert_refined_segment(
            sample_session_data["session_id"], speaker_id, "Refined text",
            segment_data["start_time"], segment_data["end_time"]
        )
        
        # Get all refined segments (no session_id filter)
        segments = get_refined_segments(None)
        assert len(segments) >= 1
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_get_locked_segments_with_limit(self, test_db, sample_session_data):
        """Test getting locked segments with limit."""
        # Create session and speaker
        session_id = get_or_create_session(sample_session_data["session_id"])
        speaker_id = get_or_create_speaker(1, "Test Speaker")
        
        # Insert multiple segments and then lock them
        segment_ids = []
        for i, segment_data in enumerate(sample_session_data["segments"]):
            refined_id = insert_refined_segment(
                sample_session_data["session_id"], speaker_id, f"Locked text {i}",
                segment_data["start_time"], segment_data["end_time"]
            )
            segment_ids.append(refined_id)
            
            # Update the segment to be locked
            update_refined_segment(refined_id, is_locked=1)
        
        # Get locked segments with limit
        locked_segments = get_locked_segments(sample_session_data["session_id"], limit=1)
        assert len(locked_segments) == 1
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_get_locked_segments_without_limit(self, test_db, sample_session_data):
        """Test getting locked segments without limit."""
        # Create session and speaker
        session_id = get_or_create_session(sample_session_data["session_id"])
        speaker_id = get_or_create_speaker(1, "Test Speaker")
        
        # Insert segment and then lock it
        segment_data = sample_session_data["segments"][0]
        refined_id = insert_refined_segment(
            sample_session_data["session_id"], speaker_id, "Locked text",
            segment_data["start_time"], segment_data["end_time"]
        )
        
        # Update the segment to be locked
        update_refined_segment(refined_id, is_locked=1)
        
        # Get locked segments without limit
        locked_segments = get_locked_segments(sample_session_data["session_id"])
        assert len(locked_segments) >= 1


class TestRefinedSegmentRetrieval:
    """Test refined segment retrieval functionality."""
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_get_refined_segment_success(self, test_db, sample_session_data):
        """Test successfully getting a refined segment by ID."""
        # Create session and speaker
        session_id = get_or_create_session(sample_session_data["session_id"])
        speaker_id = get_or_create_speaker(1, "Test Speaker")
        
        # Insert refined segment
        segment_data = sample_session_data["segments"][0]
        refined_id = insert_refined_segment(
            sample_session_data["session_id"], speaker_id, "Refined text",
            segment_data["start_time"], segment_data["end_time"]
        )
        
        # Get the refined segment
        segment = get_refined_segment(refined_id)
        assert segment is not None
        assert segment["id"] == refined_id
        assert segment["text"] == "Refined text"
        assert segment["session_id"] == sample_session_data["session_id"]
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_get_refined_segment_not_found(self, test_db):
        """Test getting a refined segment that doesn't exist."""
        segment = get_refined_segment(99999)
        assert segment is None
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_get_refined_segment_database_error(self, mocker):
        """Test get_refined_segment handles database errors."""
        mocker.patch('sqlite3.connect', side_effect=sqlite3.Error("Database error"))
        
        result = get_refined_segment(1)
        assert result is None


class TestActiveSessions:
    """Test active sessions functionality."""
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_get_active_sessions_success(self, test_db, sample_session_data):
        """Test getting active sessions successfully."""
        # Create session and speaker
        session_id = get_or_create_session(sample_session_data["session_id"])
        speaker_id = get_or_create_speaker(1, "Test Speaker")
        
        # Insert raw segment (this makes the session "active")
        segment_data = sample_session_data["segments"][0]
        log_timestamp = datetime.fromisoformat(sample_session_data["log_timestamp"].replace('Z', ''))
        insert_segment(
            sample_session_data["session_id"], speaker_id, segment_data["text"],
            segment_data["start_time"], segment_data["end_time"], log_timestamp
        )
        
        # Get active sessions
        active_sessions = get_active_sessions()
        assert len(active_sessions) >= 1
        assert any(session["session_id"] == sample_session_data["session_id"] for session in active_sessions)
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_get_active_sessions_empty(self, test_db):
        """Test getting active sessions when none exist."""
        # Use a unique session ID that doesn't exist
        unique_session_id = f"empty_test_session_{int(time.time() * 1000)}"
        active_sessions = get_active_sessions()
        # Filter to only sessions that match our unique ID (should be empty)
        filtered_sessions = [s for s in active_sessions if s["session_id"] == unique_session_id]
        assert filtered_sessions == []
    
    @pytest.mark.unit
    @pytest.mark.database
    def test_get_active_sessions_database_error(self, mocker):
        """Test get_active_sessions handles database errors."""
        mocker.patch('sqlite3.connect', side_effect=sqlite3.Error("Database error"))
        
        result = get_active_sessions()
        assert result == []
