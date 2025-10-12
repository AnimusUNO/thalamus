#!/usr/bin/env python3
"""
End-to-End Tests for Thalamus System

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
import time
import threading
import requests
from datetime import datetime, UTC
from unittest.mock import patch, Mock
import subprocess
import signal
import os

# Import the modules we're testing
from thalamus_system.core.database import (
    init_db, get_unrefined_segments, get_refined_segments,
    get_or_create_session, get_or_create_speaker, insert_segment
)
from thalamus_system.thalamus_app.transcript_refiner import TranscriptRefiner


class TestCompleteSystemE2E:
    """Test complete system end-to-end functionality."""
    
    @pytest.mark.e2e
    @pytest.mark.slow
    def test_complete_conversation_processing(self, flask_client, test_db, mock_openai_client):
        """Test processing a complete conversation from start to finish."""
        # Simulate a real conversation with multiple speakers
        conversation_data = {
            "session_id": "e2e_conversation_test",
            "log_timestamp": datetime.now(UTC).isoformat() + "Z",
            "segments": [
                {
                    "speaker_id": 1,
                    "text": "Hello everyone, welcome to our meeting today.",
                    "start_time": 0.0,
                    "end_time": 3.2
                },
                {
                    "speaker_id": 2,
                    "text": "Thank you for having me. I'm excited to discuss the project.",
                    "start_time": 3.5,
                    "end_time": 7.8
                },
                {
                    "speaker_id": 1,
                    "text": "Great! Let's start with the current status of development.",
                    "start_time": 8.0,
                    "end_time": 12.5
                },
                {
                    "speaker_id": 3,
                    "text": "We've completed about 75% of the core features.",
                    "start_time": 13.0,
                    "end_time": 16.2
                },
                {
                    "speaker_id": 2,
                    "text": "That's excellent progress. What are the remaining challenges?",
                    "start_time": 16.5,
                    "end_time": 20.1
                },
                {
                    "speaker_id": 3,
                    "text": "The main challenge is integrating the AI components with the database.",
                    "start_time": 20.5,
                    "end_time": 25.8
                }
            ]
        }
        
        # Step 1: Send conversation via webhook
        webhook_response = flask_client.post(
            '/omi',
            data=json.dumps(conversation_data),
            content_type='application/json'
        )
        assert webhook_response.status_code == 200
        
        # Step 2: Verify raw segments are stored
        raw_segments = get_unrefined_segments()
        conversation_segments = [seg for seg in raw_segments 
                               if seg['session_id'] == "e2e_conversation_test"]
        assert len(conversation_segments) == 6
        
        # Step 3: Process with transcript refiner
        refiner = TranscriptRefiner()
        with patch('thalamus_system.thalamus_app.openai_wrapper.client', mock_openai_client):
            success = refiner.process_session("e2e_conversation_test")
        assert success
        
        # Step 4: Verify refined segments are created
        refined_segments = get_refined_segments()
        conversation_refined = [seg for seg in refined_segments 
                              if seg['session_id'] == "e2e_conversation_test"]
        assert len(conversation_refined) > 0
        
        # Step 5: Verify data integrity
        with test_db as conn:
            cur = conn.cursor()
            
            # Check session exists
            cur.execute("SELECT id FROM sessions WHERE session_id = ?", 
                       ("e2e_conversation_test",))
            session_result = cur.fetchone()
            assert session_result is not None
            
            # Check speakers were created
            cur.execute("SELECT COUNT(DISTINCT speaker_id) FROM raw_segments WHERE session_id = ?",
                       (session_result[0],))
            speaker_count = cur.fetchone()[0]
            assert speaker_count == 3  # Three unique speakers
            
            # Check refined segments have proper structure
            cur.execute("""
                SELECT rs.text, rs.confidence_score, rs.source_segments
                FROM refined_segments rs
                JOIN sessions s ON rs.session_id = s.id
                WHERE s.session_id = ?
                LIMIT 1
            """, ("e2e_conversation_test",))
            refined_result = cur.fetchone()
            assert refined_result is not None
            assert refined_result[0] is not None  # text
            assert refined_result[1] is not None  # confidence_score
            assert refined_result[2] is not None  # source_segments
    
    @pytest.mark.e2e
    @pytest.mark.slow
    def test_multiple_conversations_processing(self, flask_client, test_db, mock_openai_client):
        """Test processing multiple conversations simultaneously."""
        conversations = []
        
        # Create multiple conversations
        for i in range(3):
            conversation_data = {
                "session_id": f"multi_conversation_{i}",
                "log_timestamp": datetime.now(UTC).isoformat() + "Z",
                "segments": [
                    {
                        "speaker_id": 1,
                        "text": f"Conversation {i} - Speaker 1 talking",
                        "start_time": 0.0,
                        "end_time": 2.0
                    },
                    {
                        "speaker_id": 2,
                        "text": f"Conversation {i} - Speaker 2 responding",
                        "start_time": 2.5,
                        "end_time": 4.5
                    }
                ]
            }
            conversations.append(conversation_data)
        
        # Send all conversations via webhook
        responses = []
        for conversation in conversations:
            response = flask_client.post(
                '/omi',
                data=json.dumps(conversation),
                content_type='application/json'
            )
            responses.append(response)
        
        # Verify all webhook responses succeeded
        for response in responses:
            assert response.status_code == 200
        
        # Process all conversations with transcript refiner
        refiner = TranscriptRefiner()
        with patch('thalamus_system.thalamus_app.openai_wrapper.client', mock_openai_client):
            for i in range(3):
                success = refiner.process_session(f"multi_conversation_{i}")
                assert success
        
        # Verify all conversations were processed
        for i in range(3):
            session_id = f"multi_conversation_{i}"
            
            # Check raw segments
            raw_segments = get_unrefined_segments()
            session_raw = [seg for seg in raw_segments if seg['session_id'] == session_id]
            assert len(session_raw) == 2
            
            # Check refined segments
            refined_segments = get_refined_segments()
            session_refined = [seg for seg in refined_segments if seg['session_id'] == session_id]
            assert len(session_refined) > 0
    
    @pytest.mark.e2e
    @pytest.mark.slow
    def test_error_recovery_e2e(self, flask_client, test_db):
        """Test error recovery in end-to-end scenarios."""
        # Test with malformed data
        malformed_data = {
            "session_id": "error_recovery_test",
            "segments": [
                {
                    "speaker_id": 1,
                    "text": "Valid segment",
                    "start_time": 0.0,
                    "end_time": 2.0
                },
                {
                    "speaker_id": 2,
                    "text": "",  # Empty text
                    "start_time": 2.0,
                    "end_time": 4.0
                },
                {
                    "speaker_id": 3,
                    "text": "Another valid segment",
                    "start_time": 4.0,
                    "end_time": 6.0
                }
            ],
            "log_timestamp": datetime.now(UTC).isoformat() + "Z"
        }
        
        # Send malformed data
        response = flask_client.post(
            '/omi',
            data=json.dumps(malformed_data),
            content_type='application/json'
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 422]
        
        # Verify system is still functional
        health_response = flask_client.get('/health')
        assert health_response.status_code == 200
        
        # Verify valid segments were processed
        raw_segments = get_unrefined_segments()
        session_segments = [seg for seg in raw_segments 
                           if seg['session_id'] == "error_recovery_test"]
        # Should have processed at least the valid segments
        assert len(session_segments) >= 2


class TestSystemResilienceE2E:
    """Test system resilience and error handling."""
    
    @pytest.mark.e2e
    @pytest.mark.slow
    def test_high_load_processing(self, flask_client, test_db, mock_openai_client):
        """Test system under high load."""
        # Create many concurrent requests
        requests_data = []
        for i in range(20):  # 20 concurrent requests
            request_data = {
                "session_id": f"load_test_{i}",
                "log_timestamp": datetime.now(UTC).isoformat() + "Z",
                "segments": [
                    {
                        "speaker_id": 1,
                        "text": f"Load test segment {i}",
                        "start_time": 0.0,
                        "end_time": 1.0
                    }
                ]
            }
            requests_data.append(request_data)
        
        # Send all requests
        responses = []
        for request_data in requests_data:
            response = flask_client.post(
                '/omi',
                data=json.dumps(request_data),
                content_type='application/json'
            )
            responses.append(response)
        
        # Verify most requests succeeded (allow for some failures under load)
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= 15  # At least 75% should succeed
        
        # Process successful sessions
        refiner = TranscriptRefiner()
        with patch('thalamus_system.thalamus_app.openai_wrapper.client', mock_openai_client):
            processed_count = 0
            for i in range(20):
                try:
                    success = refiner.process_session(f"load_test_{i}")
                    if success:
                        processed_count += 1
                except Exception:
                    # Some failures are expected under load
                    pass
        
        # Verify some sessions were processed
        assert processed_count > 0
        
        # Verify system is still healthy
        health_response = flask_client.get('/health')
        assert health_response.status_code == 200
    
    @pytest.mark.e2e
    @pytest.mark.slow
    def test_database_corruption_recovery(self, test_db):
        """Test recovery from database corruption scenarios."""
        # Create some test data
        session_id = get_or_create_session("corruption_test_session")
        speaker_id = get_or_create_speaker(1, "Corruption Test Speaker")
        
        log_timestamp = datetime.now(UTC)
        segment_id = insert_segment(
            session_id, speaker_id, "Test segment for corruption test",
            0.0, 2.0, log_timestamp
        )
        
        # Verify data exists
        segments = get_unrefined_segments()
        assert len(segments) > 0
        
        # Simulate database issues by corrupting a connection
        with patch('sqlite3.connect') as mock_connect:
            # First call succeeds, second fails, third succeeds
            mock_connect.side_effect = [
                test_db,
                Exception("Database corruption"),
                test_db
            ]
            
            # Should handle first call
            segments = get_unrefined_segments()
            assert len(segments) > 0
            
            # Second call should fail gracefully
            try:
                segments = get_unrefined_segments()
            except Exception:
                pass  # Expected to fail
            
            # Third call should succeed
            segments = get_unrefined_segments()
            assert len(segments) > 0


class TestRealWorldScenariosE2E:
    """Test real-world usage scenarios."""
    
    @pytest.mark.e2e
    @pytest.mark.slow
    def test_meeting_transcription_scenario(self, flask_client, test_db, mock_openai_client):
        """Test realistic meeting transcription scenario."""
        # Simulate a 30-minute meeting with 4 speakers
        meeting_data = {
            "session_id": "meeting_2025_01_15",
            "log_timestamp": datetime.now(UTC).isoformat() + "Z",
            "segments": []
        }
        
        # Generate realistic meeting segments
        speakers = ["Alice", "Bob", "Charlie", "Diana"]
        current_time = 0.0
        
        # Meeting introduction
        meeting_data["segments"].extend([
            {
                "speaker_id": 1,
                "text": "Good morning everyone, welcome to our weekly team meeting.",
                "start_time": current_time,
                "end_time": current_time + 3.5
            },
            {
                "speaker_id": 2,
                "text": "Thanks Alice, I'm excited to discuss our progress this week.",
                "start_time": current_time + 4.0,
                "end_time": current_time + 7.2
            }
        ])
        current_time += 8.0
        
        # Discussion segments
        discussion_topics = [
            "Let's review the project timeline and milestones.",
            "I think we're ahead of schedule on the frontend development.",
            "The backend API integration is taking longer than expected.",
            "We should prioritize the database optimization tasks.",
            "I agree, that's our biggest bottleneck right now.",
            "What about the testing phase? When do we start that?",
            "We should begin testing next week if everything goes well.",
            "I'll prepare the test cases and documentation."
        ]
        
        for i, topic in enumerate(discussion_topics):
            speaker_id = (i % 4) + 1
            duration = len(topic.split()) * 0.3  # Rough duration based on word count
            
            meeting_data["segments"].append({
                "speaker_id": speaker_id,
                "text": topic,
                "start_time": current_time,
                "end_time": current_time + duration
            })
            current_time += duration + 0.5  # Small pause between speakers
        
        # Meeting conclusion
        meeting_data["segments"].extend([
            {
                "speaker_id": 1,
                "text": "Great discussion everyone. Let's reconvene next week.",
                "start_time": current_time,
                "end_time": current_time + 3.0
            },
            {
                "speaker_id": 3,
                "text": "Sounds good, I'll send out the action items by tomorrow.",
                "start_time": current_time + 3.5,
                "end_time": current_time + 6.0
            }
        ])
        
        # Process the meeting
        webhook_response = flask_client.post(
            '/omi',
            data=json.dumps(meeting_data),
            content_type='application/json'
        )
        assert webhook_response.status_code == 200
        
        # Verify meeting data
        raw_segments = get_unrefined_segments()
        meeting_segments = [seg for seg in raw_segments 
                           if seg['session_id'] == "meeting_2025_01_15"]
        assert len(meeting_segments) == len(meeting_data["segments"])
        
        # Process with transcript refiner
        refiner = TranscriptRefiner()
        with patch('thalamus_system.thalamus_app.openai_wrapper.client', mock_openai_client):
            success = refiner.process_session("meeting_2025_01_15")
        assert success
        
        # Verify refined segments
        refined_segments = get_refined_segments()
        meeting_refined = [seg for seg in refined_segments 
                          if seg['session_id'] == "meeting_2025_01_15"]
        assert len(meeting_refined) > 0
        
        # Verify meeting metadata
        with test_db as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT COUNT(DISTINCT speaker_id) FROM raw_segments rs
                JOIN sessions s ON rs.session_id = s.id
                WHERE s.session_id = ?
            """, ("meeting_2025_01_15",))
            speaker_count = cur.fetchone()[0]
            assert speaker_count == 4
            
            # Check meeting duration
            cur.execute("""
                SELECT MAX(end_time) - MIN(start_time) FROM raw_segments rs
                JOIN sessions s ON rs.session_id = s.id
                WHERE s.session_id = ?
            """, ("meeting_2025_01_15",))
            duration = cur.fetchone()[0]
            assert duration > 0  # Meeting should have some duration
    
    @pytest.mark.e2e
    @pytest.mark.slow
    def test_interview_transcription_scenario(self, flask_client, test_db, mock_openai_client):
        """Test realistic interview transcription scenario."""
        interview_data = {
            "session_id": "interview_candidate_123",
            "log_timestamp": datetime.now(UTC).isoformat() + "Z",
            "segments": [
                {
                    "speaker_id": 1,
                    "text": "Thank you for coming in today. Can you tell me about your experience with Python?",
                    "start_time": 0.0,
                    "end_time": 4.2
                },
                {
                    "speaker_id": 2,
                    "text": "Absolutely. I've been working with Python for about five years now, primarily in web development and data analysis.",
                    "start_time": 4.5,
                    "end_time": 12.8
                },
                {
                    "speaker_id": 1,
                    "text": "That's great. What frameworks have you worked with?",
                    "start_time": 13.0,
                    "end_time": 16.5
                },
                {
                    "speaker_id": 2,
                    "text": "I've used Django extensively for web applications, and Flask for smaller projects. I'm also familiar with FastAPI for API development.",
                    "start_time": 17.0,
                    "end_time": 28.2
                },
                {
                    "speaker_id": 1,
                    "text": "Excellent. How about testing? What's your approach to writing tests?",
                    "start_time": 28.5,
                    "end_time": 33.1
                },
                {
                    "speaker_id": 2,
                    "text": "I believe in comprehensive testing. I use pytest for unit tests and try to maintain high code coverage. I also write integration tests for critical paths.",
                    "start_time": 33.5,
                    "end_time": 42.8
                }
            ]
        }
        
        # Process the interview
        webhook_response = flask_client.post(
            '/omi',
            data=json.dumps(interview_data),
            content_type='application/json'
        )
        assert webhook_response.status_code == 200
        
        # Process with transcript refiner
        refiner = TranscriptRefiner()
        with patch('thalamus_system.thalamus_app.openai_wrapper.client', mock_openai_client):
            success = refiner.process_session("interview_candidate_123")
        assert success
        
        # Verify interview data integrity
        raw_segments = get_unrefined_segments()
        interview_segments = [seg for seg in raw_segments 
                             if seg['session_id'] == "interview_candidate_123"]
        assert len(interview_segments) == 6
        
        # Verify refined segments capture the conversation flow
        refined_segments = get_refined_segments()
        interview_refined = [seg for seg in refined_segments 
                            if seg['session_id'] == "interview_candidate_123"]
        assert len(interview_refined) > 0
        
        # Verify conversation flow is maintained
        with test_db as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT rs.text, rs.start_time, rs.end_time
                FROM raw_segments rs
                JOIN sessions s ON rs.session_id = s.id
                WHERE s.session_id = ?
                ORDER BY rs.start_time
            """, ("interview_candidate_123",))
            
            segments = cur.fetchall()
            assert len(segments) == 6
            
            # Verify chronological order
            for i in range(len(segments) - 1):
                assert segments[i][2] <= segments[i + 1][1]  # end_time <= next start_time


class TestSystemMonitoringE2E:
    """Test system monitoring and observability."""
    
    @pytest.mark.e2e
    def test_health_monitoring_e2e(self, flask_client):
        """Test health monitoring endpoints in real scenarios."""
        # Test basic health
        health_response = flask_client.get('/health')
        assert health_response.status_code == 200
        health_data = health_response.get_json()
        assert health_data['data']['status'] == 'healthy'
        
        # Test detailed health
        detailed_response = flask_client.get('/health/detailed')
        assert detailed_response.status_code == 200
        detailed_data = detailed_response.get_json()
        assert 'checks' in detailed_data['data']
        assert 'database' in detailed_data['data']['checks']
        
        # Test readiness
        ready_response = flask_client.get('/ready')
        assert ready_response.status_code == 200
        
        # Test metrics
        metrics_response = flask_client.get('/metrics')
        assert metrics_response.status_code == 200
        metrics_data = metrics_response.get_json()
        assert 'uptime_seconds' in metrics_data['data']
        assert 'timestamp' in metrics_data['data']
    
    @pytest.mark.e2e
    def test_logging_and_monitoring_e2e(self, flask_client, caplog):
        """Test logging and monitoring in end-to-end scenarios."""
        with caplog.at_level("INFO"):
            # Send a request
            test_data = {
                "session_id": "logging_test_session",
                "segments": [{"speaker_id": 1, "text": "Test logging", "start_time": 0.0, "end_time": 1.0}],
                "log_timestamp": datetime.now(UTC).isoformat() + "Z"
            }
            
            response = flask_client.post(
                '/omi',
                data=json.dumps(test_data),
                content_type='application/json'
            )
            
            assert response.status_code == 200
            
            # Check health
            health_response = flask_client.get('/health')
            assert health_response.status_code == 200
        
        # Verify logs were generated
        log_messages = [record.message for record in caplog.records]
        assert any("Incoming POST" in msg for msg in log_messages)
        assert any("Successfully received webhook data" in msg for msg in log_messages)
