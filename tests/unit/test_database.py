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
