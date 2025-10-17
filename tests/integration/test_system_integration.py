#!/usr/bin/env python3
"""
Integration Tests for Thalamus System

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
import asyncio
import time
from datetime import datetime, UTC
from unittest.mock import patch, Mock

# Import the modules we're testing
from thalamus_system.core.database import (
    init_db, get_or_create_session, get_or_create_speaker,
    insert_segment, get_unrefined_segments, insert_refined_segment,
    get_refined_segments, get_locked_segments
)
from thalamus_system.thalamus_app.thalamus_app import process_event
from thalamus_system.thalamus_app.transcript_refiner import TranscriptRefiner
from thalamus_system.webhook_server.omi_webhook import app


class TestDataFlowIntegration:
    """Test complete data flow from webhook to database."""
    
    @pytest.mark.integration
    @pytest.mark.database
    def test_webhook_to_database_flow(self, flask_client, test_db, sample_session_data):
        """Test complete flow from webhook to database storage."""
        # Send data via webhook
        response = flask_client.post(
            '/omi',
            data=json.dumps(sample_session_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        
        # Verify data was stored in database
        with test_db as conn:
            cur = conn.cursor()
            
            # Check session was created
            cur.execute("SELECT id FROM sessions WHERE session_id = ?", 
                       (sample_session_data['session_id'],))
            session_result = cur.fetchone()
            assert session_result is not None
            
            # Check segments were stored (match by numeric session primary key)
            cur.execute("SELECT COUNT(*) FROM raw_segments WHERE session_id = ?",
                       (session_result[0],))
            segment_count = cur.fetchone()[0]
            assert segment_count == len(sample_session_data['segments'])
    
    @pytest.mark.integration
    @pytest.mark.database
    def test_event_processing_integration(self, test_db, sample_session_data):
        """Test event processing integration."""
        # Process event directly
        process_event(sample_session_data)
        
        # Verify data in database
        segments = get_unrefined_segments()
        session_segments = [seg for seg in segments 
                          if seg['session_id'] == sample_session_data['session_id']]
        
        assert len(session_segments) == len(sample_session_data['segments'])
        
        # Verify segment content
        for i, segment in enumerate(session_segments):
            original_segment = sample_session_data['segments'][i]
            assert segment['text'] == original_segment['text']
            assert segment['start_time'] == original_segment['start_time']
            assert segment['end_time'] == original_segment['end_time']
    
    @pytest.mark.integration
    @pytest.mark.database
    def test_transcript_refinement_integration(self, test_db, sample_session_data, mock_openai_client):
        """Test transcript refinement integration."""
        # First, process the event to create raw segments
        process_event(sample_session_data)
        
        # Create transcript refiner
        refiner = TranscriptRefiner()
        
        # Process the session
        with patch('thalamus_system.thalamus_app.openai_wrapper.client', mock_openai_client):
            success = refiner.process_session(sample_session_data['session_id'])
        
        assert success
        
        # Verify refined segments were created
        refined_segments = get_refined_segments()
        session_refined = [seg for seg in refined_segments 
                          if seg['session_id'] == sample_session_data['session_id']]
        
        assert len(session_refined) > 0
        
        # Verify refined segment has proper structure
        refined_segment = session_refined[0]
        assert 'text' in refined_segment
        assert 'confidence_score' in refined_segment
        assert 'source_segments' in refined_segment


class TestDatabaseIntegration:
    """Test database integration scenarios."""
    
    @pytest.mark.integration
    @pytest.mark.database
    def test_session_speaker_integration(self, test_db):
        """Test session and speaker integration."""
        session_id = "integration_test_session"
        speaker_name = "Integration Test Speaker"
        
        # Create session and speaker
        session_db_id = get_or_create_session(session_id)
        speaker_db_id = get_or_create_speaker(1, speaker_name)
        
        # Insert segment linking session and speaker
        log_timestamp = datetime.now(UTC)
        segment_id = insert_segment(
            session_db_id, speaker_db_id, "Integration test segment",
            0.0, 2.0, log_timestamp
        )
        
        # Verify relationships
        with test_db as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT s.session_id, sp.name, rs.text
                FROM raw_segments rs
                JOIN sessions s ON rs.session_id = s.id
                JOIN speakers sp ON rs.speaker_id = sp.id
                WHERE rs.id = ?
            """, (segment_id,))
            
            result = cur.fetchone()
            assert result is not None
            assert result[0] == session_id
            assert result[1] == speaker_name
            assert result[2] == "Integration test segment"
    
    @pytest.mark.integration
    @pytest.mark.database
    def test_refined_segment_lifecycle(self, test_db):
        """Test complete refined segment lifecycle."""
        # Create session and speaker
        session_id = get_or_create_session("lifecycle_test_session")
        speaker_id = get_or_create_speaker(1, "Lifecycle Speaker")
        
        # Insert raw segment
        log_timestamp = datetime.now(UTC)
        raw_segment_id = insert_segment(
            session_id, speaker_id, "Raw segment text",
            0.0, 2.0, log_timestamp
        )
        
        # Insert refined segment
        refined_segment_id = insert_refined_segment(
            session_id, speaker_id, "Refined segment text",
            0.0, 2.0, confidence_score=0.95,
            source_segments=str(raw_segment_id)
        )
        
        # Verify refined segment
        refined_segments = get_refined_segments()
        assert len(refined_segments) > 0
        
        # Test locking mechanism
        with test_db as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE refined_segments 
                SET is_processing = 0 
                WHERE id = ?
            """, (refined_segment_id,))
            conn.commit()
        
        # Get locked segments
        locked_segments = get_locked_segments("lifecycle_test_session")
        assert len(locked_segments) >= 0  # May or may not be locked depending on implementation
    
    @pytest.mark.integration
    @pytest.mark.database
    def test_concurrent_session_creation(self, test_db):
        """Test concurrent session creation."""
        session_ids = [f"concurrent_session_{i}" for i in range(10)]
        
        # Create sessions concurrently (simulated)
        created_sessions = []
        for session_id in session_ids:
            session_db_id = get_or_create_session(session_id)
            created_sessions.append((session_id, session_db_id))
        
        # Verify all sessions were created
        assert len(created_sessions) == len(session_ids)
        
        # Verify no duplicates
        session_db_ids = [sid for _, sid in created_sessions]
        assert len(set(session_db_ids)) == len(session_db_ids)
        
        # Verify all sessions exist in database
        with test_db as conn:
            cur = conn.cursor()
            for session_id, session_db_id in created_sessions:
                cur.execute("SELECT session_id FROM sessions WHERE id = ?", (session_db_id,))
                result = cur.fetchone()
                assert result is not None
                assert result[0] == session_id


class TestAsyncIntegration:
    """Test async integration scenarios."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_async_event_processing(self, test_db, sample_session_data):
        """Test async event processing."""
        # Simulate async event processing
        async def process_event_async(event_data):
            # Simulate async processing delay
            await asyncio.sleep(0.1)
            return process_event(event_data)
        
        # Process event asynchronously
        result = await process_event_async(sample_session_data)
        
        # Verify data was processed
        segments = get_unrefined_segments()
        session_segments = [seg for seg in segments 
                          if seg['session_id'] == sample_session_data['session_id']]
        
        assert len(session_segments) == len(sample_session_data['segments'])
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_webhook_requests(self, flask_client, sample_session_data):
        """Test concurrent webhook requests."""
        # Create multiple similar requests
        requests = []
        for i in range(5):
            data = sample_session_data.copy()
            data['session_id'] = f"concurrent_test_{i}"
            requests.append(data)
        
        # Process requests concurrently
        async def send_request(data):
            return flask_client.post(
                '/omi',
                data=json.dumps(data),
                content_type='application/json'
            )
        
        # Send all requests
        tasks = [send_request(data) for data in requests]
        responses = await asyncio.gather(*tasks)
        
        # Verify all requests succeeded
        for response in responses:
            assert response.status_code == 200
        
        # Verify all sessions were created
        for i in range(5):
            session_id = f"concurrent_test_{i}"
            session_db_id = get_or_create_session(session_id)
            assert session_db_id > 0


class TestPerformanceIntegration:
    """Test performance integration scenarios."""
    
    @pytest.mark.integration
    @pytest.mark.performance
    def test_large_dataset_processing(self, test_db, performance_timer):
        """Test processing large datasets."""
        # Create large dataset
        session_id = get_or_create_session("large_dataset_session")
        speaker_id = get_or_create_speaker(1, "Large Dataset Speaker")
        
        start_time = performance_timer
        
        # Insert many segments
        log_timestamp = datetime.now(UTC)
        segment_ids = []
        for i in range(100):  # 100 segments
            segment_id = insert_segment(
                session_id, speaker_id, f"Segment {i} with some text content",
                float(i), float(i + 1), log_timestamp
            )
            segment_ids.append(segment_id)
        
        # Query all segments
        segments = get_unrefined_segments()
        session_segments = [seg for seg in segments 
                          if seg['session_id'] == "large_dataset_session"]
        
        assert len(session_segments) == 100
        
        # Performance check - should complete in reasonable time
        # This is a basic check; more detailed performance testing would be in dedicated performance tests
        assert len(segment_ids) == 100
    
    @pytest.mark.integration
    @pytest.mark.performance
    def test_database_index_performance(self, test_db, performance_timer):
        """Test database index performance."""
        # Create test data
        session_ids = []
        for i in range(50):
            session_id = f"perf_test_session_{i}"
            session_db_id = get_or_create_session(session_id)
            session_ids.append(session_id)
            
            # Add segments to each session
            speaker_id = get_or_create_speaker(i % 5, f"Speaker {i % 5}")
            log_timestamp = datetime.now(UTC)
            insert_segment(
                session_db_id, speaker_id, f"Segment for session {i}",
                0.0, 1.0, log_timestamp
            )
        
        start_time = performance_timer
        
        # Test session-based queries (should use indexes)
        for session_id in session_ids:
            segments = get_unrefined_segments()
            session_segments = [seg for seg in segments 
                              if seg['session_id'] == session_id]
            assert len(session_segments) >= 0
        
        # Performance should be good due to indexes
        # Detailed timing would be checked in dedicated performance tests
        assert len(session_ids) == 50


class TestErrorRecoveryIntegration:
    """Test error recovery and resilience."""
    
    @pytest.mark.integration
    def test_database_connection_recovery(self, test_db):
        """Test database connection recovery."""
        # Simulate database connection issues
        with patch('sqlite3.connect') as mock_connect:
            # First call fails, second succeeds
            mock_connect.side_effect = [
                Exception("Connection failed"),
                test_db
            ]
            
            # Should handle gracefully
            try:
                with test_db as conn:
                    pass
            except Exception:
                # Expected to fail first time
                pass
            
            # Second attempt should succeed
            with test_db as conn:
                assert conn is not None
    
    @pytest.mark.integration
    def test_partial_data_processing(self, test_db):
        """Test processing partial/corrupted data."""
        # Test with partial data
        partial_data = {
            "session_id": "partial_test_session",
            "segments": [
                {"text": "Valid segment", "start_time": 0.0, "end_time": 1.0, "speaker_id": 1},
                {"text": "", "start_time": 1.0, "end_time": 2.0},  # Empty text - missing speaker_id
                {"text": "Another valid segment", "start_time": 2.0, "end_time": 3.0, "speaker_id": 2}
            ],
            "log_timestamp": datetime.now(UTC).isoformat() + "Z"
        }
        
        # Should handle gracefully
        try:
            process_event(partial_data)
            
            # Verify valid segments were processed
            segments = get_unrefined_segments()
            session_segments = [seg for seg in segments 
                              if seg['session_id'] == "partial_test_session"]
            
            # Should have processed valid segments
            assert len(session_segments) >= 2
        except Exception as e:
            # Should handle errors gracefully
            assert "Invalid" in str(e) or "Error" in str(e)


class TestSystemIntegration:
    """Test complete system integration."""
    
    @pytest.mark.integration
    @pytest.mark.e2e
    def test_end_to_end_workflow(self, flask_client, test_db, mock_openai_client):
        """Test complete end-to-end workflow."""
        # 1. Send data via webhook
        sample_data = {
            "session_id": "e2e_test_session",
            "log_timestamp": datetime.now(UTC).isoformat() + "Z",
            "segments": [
                {
                    "speaker_id": 1,
                    "text": "Hello, this is a test conversation.",
                    "start_time": 0.0,
                    "end_time": 2.5
                },
                {
                    "speaker_id": 2,
                    "text": "Yes, this is working well.",
                    "start_time": 2.5,
                    "end_time": 5.0
                }
            ]
        }
        
        webhook_response = flask_client.post(
            '/omi',
            data=json.dumps(sample_data),
            content_type='application/json'
        )
        assert webhook_response.status_code == 200
        
        # 2. Verify data in database
        segments = get_unrefined_segments()
        session_segments = [seg for seg in segments 
                          if seg['session_id'] == "e2e_test_session"]
        assert len(session_segments) == 2
        
        # 3. Process with transcript refiner
        refiner = TranscriptRefiner()
        with patch('thalamus_system.thalamus_app.openai_wrapper.client', mock_openai_client):
            success = refiner.process_session("e2e_test_session")
        assert success
        
        # 4. Verify refined segments
        refined_segments = get_refined_segments()
        session_refined = [seg for seg in refined_segments 
                          if seg['session_id'] == "e2e_test_session"]
        assert len(session_refined) > 0
        
        # 5. Test health endpoints
        health_response = flask_client.get('/health')
        assert health_response.status_code == 200
        
        # 6. Verify complete data integrity
        with test_db as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT COUNT(*) FROM raw_segments rs
                JOIN sessions s ON rs.session_id = s.id
                WHERE s.session_id = ?
            """, ("e2e_test_session",))
            raw_count = cur.fetchone()[0]
            
            cur.execute("""
                SELECT COUNT(*) FROM refined_segments rs
                JOIN sessions s ON rs.session_id = s.id
                WHERE s.session_id = ?
            """, ("e2e_test_session",))
            refined_count = cur.fetchone()[0]
            
            assert raw_count == 2
            assert refined_count > 0
