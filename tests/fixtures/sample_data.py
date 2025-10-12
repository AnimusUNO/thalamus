#!/usr/bin/env python3
"""
Test Fixtures and Sample Data for Thalamus Testing Suite

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

import json
import os
from datetime import datetime, UTC
from typing import Dict, List, Any


# Sample session data for testing
SAMPLE_SESSION_DATA = {
    "session_id": "test_session_12345",
    "log_timestamp": "2025-01-15T10:30:00.000Z",
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
        }
    ]
}

# Sample meeting data
SAMPLE_MEETING_DATA = {
    "session_id": "meeting_2025_01_15",
    "log_timestamp": "2025-01-15T14:00:00.000Z",
    "segments": [
        {
            "speaker_id": 1,
            "text": "Good morning everyone, welcome to our weekly team meeting.",
            "start_time": 0.0,
            "end_time": 4.5
        },
        {
            "speaker_id": 2,
            "text": "Thanks Alice, I'm excited to discuss our progress this week.",
            "start_time": 5.0,
            "end_time": 9.2
        },
        {
            "speaker_id": 1,
            "text": "Let's start with the project timeline and milestones.",
            "start_time": 10.0,
            "end_time": 14.5
        },
        {
            "speaker_id": 3,
            "text": "I think we're ahead of schedule on the frontend development.",
            "start_time": 15.0,
            "end_time": 19.8
        },
        {
            "speaker_id": 4,
            "text": "The backend API integration is taking longer than expected.",
            "start_time": 20.5,
            "end_time": 25.2
        },
        {
            "speaker_id": 1,
            "text": "We should prioritize the database optimization tasks.",
            "start_time": 26.0,
            "end_time": 30.5
        },
        {
            "speaker_id": 2,
            "text": "I agree, that's our biggest bottleneck right now.",
            "start_time": 31.0,
            "end_time": 35.8
        },
        {
            "speaker_id": 3,
            "text": "What about the testing phase? When do we start that?",
            "start_time": 36.5,
            "end_time": 41.2
        },
        {
            "speaker_id": 1,
            "text": "We should begin testing next week if everything goes well.",
            "start_time": 42.0,
            "end_time": 47.5
        },
        {
            "speaker_id": 4,
            "text": "I'll prepare the test cases and documentation.",
            "start_time": 48.0,
            "end_time": 52.8
        },
        {
            "speaker_id": 1,
            "text": "Great discussion everyone. Let's reconvene next week.",
            "start_time": 54.0,
            "end_time": 58.5
        }
    ]
}

# Sample interview data
SAMPLE_INTERVIEW_DATA = {
    "session_id": "interview_candidate_456",
    "log_timestamp": "2025-01-15T15:30:00.000Z",
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
        },
        {
            "speaker_id": 1,
            "text": "That's exactly what we're looking for. How do you handle database design?",
            "start_time": 43.0,
            "end_time": 48.5
        },
        {
            "speaker_id": 2,
            "text": "I've designed both relational and NoSQL databases. I focus on normalization for relational databases and consider query patterns for optimization.",
            "start_time": 49.0,
            "end_time": 58.2
        },
        {
            "speaker_id": 1,
            "text": "Perfect. Do you have any questions for us?",
            "start_time": 59.0,
            "end_time": 62.5
        },
        {
            "speaker_id": 2,
            "text": "Yes, I'd like to know more about the team structure and growth opportunities.",
            "start_time": 63.0,
            "end_time": 68.8
        }
    ]
}

# Sample speaker data
SAMPLE_SPEAKERS = [
    {"id": 1, "name": "Alice Johnson", "is_user": True},
    {"id": 2, "name": "Bob Smith", "is_user": False},
    {"id": 3, "name": "Charlie Brown", "is_user": False},
    {"id": 4, "name": "Diana Prince", "is_user": False}
]

# Sample refined segment data
SAMPLE_REFINED_SEGMENTS = [
    {
        "session_id": "test_session_12345",
        "refined_speaker_id": 1,
        "text": "Hello everyone, welcome to our meeting today. We have a lot to discuss.",
        "start_time": 0.0,
        "end_time": 3.2,
        "confidence_score": 0.95,
        "source_segments": "[1, 2]",
        "metadata": '{"processing_time": 1.2, "model_version": "gpt-4"}',
        "is_processing": 0
    },
    {
        "session_id": "test_session_12345",
        "refined_speaker_id": 2,
        "text": "Thank you for having me. I'm excited to discuss the project and share our progress.",
        "start_time": 3.5,
        "end_time": 7.8,
        "confidence_score": 0.92,
        "source_segments": "[3]",
        "metadata": '{"processing_time": 0.8, "model_version": "gpt-4"}',
        "is_processing": 0
    }
]

# Sample error responses
SAMPLE_ERROR_RESPONSES = {
    "invalid_json": {
        "status": "error",
        "message": "Invalid JSON format",
        "timestamp": "2025-01-15T10:30:00.000Z",
        "code": 400,
        "details": {
            "json_error": "Expecting value: line 1 column 1 (char 0)"
        }
    },
    "missing_session_id": {
        "status": "error",
        "message": "Validation failed",
        "timestamp": "2025-01-15T10:30:00.000Z",
        "code": 422,
        "errors": {
            "session_id": "session_id is required"
        }
    },
    "missing_segments": {
        "status": "error",
        "message": "Validation failed",
        "timestamp": "2025-01-15T10:30:00.000Z",
        "code": 422,
        "errors": {
            "segments": "segments array is required"
        }
    },
    "empty_segments": {
        "status": "error",
        "message": "Validation failed",
        "timestamp": "2025-01-15T10:30:00.000Z",
        "code": 422,
        "errors": {
            "segments": "segments array cannot be empty"
        }
    },
    "wrong_content_type": {
        "status": "error",
        "message": "Content-Type must be application/json",
        "timestamp": "2025-01-15T10:30:00.000Z",
        "code": 400
    },
    "payload_too_large": {
        "status": "error",
        "message": "Request too large. Maximum size is 10MB",
        "timestamp": "2025-01-15T10:30:00.000Z",
        "code": 413,
        "details": {
            "max_size_mb": 10,
            "received_size_bytes": 15728640
        }
    },
    "internal_server_error": {
        "status": "error",
        "message": "Internal server error",
        "timestamp": "2025-01-15T10:30:00.000Z",
        "code": 500,
        "details": {
            "error_type": "DatabaseError"
        }
    }
}

# Sample success responses
SAMPLE_SUCCESS_RESPONSES = {
    "webhook_success": {
        "status": "success",
        "message": "Data received and processed successfully",
        "timestamp": "2025-01-15T10:30:00.000Z",
        "data": {
            "session_id": "test_session_12345",
            "segments_processed": 5,
            "timestamp": "2025-01-15T10:30:00.000Z"
        }
    },
    "health_check": {
        "status": "success",
        "message": "Service is healthy",
        "timestamp": "2025-01-15T10:30:00.000Z",
        "data": {
            "status": "healthy",
            "uptime_seconds": 3600,
            "version": "1.0.0",
            "timestamp": "2025-01-15T10:30:00.000Z"
        }
    },
    "detailed_health": {
        "status": "success",
        "message": "Service is healthy",
        "timestamp": "2025-01-15T10:30:00.000Z",
        "data": {
            "status": "healthy",
            "timestamp": "2025-01-15T10:30:00.000Z",
            "version": "1.0.0",
            "uptime_seconds": 3600,
            "checks": {
                "database": "healthy",
                "env_OPENAI_API_KEY": "healthy",
                "config": {
                    "max_request_size_mb": 10,
                    "max_json_size_mb": 5
                }
            }
        }
    },
    "readiness_check": {
        "status": "success",
        "message": "Service is ready",
        "timestamp": "2025-01-15T10:30:00.000Z",
        "data": {
            "status": "ready"
        }
    },
    "metrics": {
        "status": "success",
        "message": "Metrics retrieved",
        "timestamp": "2025-01-15T10:30:00.000Z",
        "data": {
            "uptime_seconds": 3600,
            "uptime_hours": 1.0,
            "max_request_size_mb": 10,
            "max_json_size_mb": 5,
            "timestamp": "2025-01-15T10:30:00.000Z"
        }
    }
}

# Sample OpenAI API responses
SAMPLE_OPENAI_RESPONSES = {
    "successful_refinement": {
        "choices": [
            {
                "message": {
                    "content": "Hello everyone, welcome to our meeting today. We have a lot to discuss and I'm excited to hear everyone's input."
                }
            }
        ],
        "usage": {
            "prompt_tokens": 150,
            "completion_tokens": 25,
            "total_tokens": 175
        }
    },
    "meeting_refinement": {
        "choices": [
            {
                "message": {
                    "content": "Good morning everyone, welcome to our weekly team meeting. I'm excited to discuss our progress and plan for the upcoming week."
                }
            }
        ],
        "usage": {
            "prompt_tokens": 200,
            "completion_tokens": 30,
            "total_tokens": 230
        }
    },
    "interview_refinement": {
        "choices": [
            {
                "message": {
                    "content": "Thank you for coming in today. Can you tell me about your experience with Python and what projects you've worked on?"
                }
            }
        ],
        "usage": {
            "prompt_tokens": 180,
            "completion_tokens": 28,
            "total_tokens": 208
        }
    }
}

# Sample database records
SAMPLE_DATABASE_RECORDS = {
    "sessions": [
        {"id": 1, "session_id": "test_session_12345", "created_at": "2025-01-15T10:30:00.000Z"},
        {"id": 2, "session_id": "meeting_2025_01_15", "created_at": "2025-01-15T14:00:00.000Z"},
        {"id": 3, "session_id": "interview_candidate_456", "created_at": "2025-01-15T15:30:00.000Z"}
    ],
    "speakers": [
        {"id": 1, "name": "Alice Johnson", "created_at": "2025-01-15T10:30:00.000Z"},
        {"id": 2, "name": "Bob Smith", "created_at": "2025-01-15T10:30:00.000Z"},
        {"id": 3, "name": "Charlie Brown", "created_at": "2025-01-15T10:30:00.000Z"},
        {"id": 4, "name": "Diana Prince", "created_at": "2025-01-15T10:30:00.000Z"}
    ],
    "raw_segments": [
        {
            "id": 1,
            "session_id": 1,
            "speaker_id": 1,
            "text": "Hello everyone, welcome to our meeting today.",
            "start_time": 0.0,
            "end_time": 3.2,
            "timestamp": "2025-01-15T10:30:00.000Z"
        },
        {
            "id": 2,
            "session_id": 1,
            "speaker_id": 2,
            "text": "Thank you for having me. I'm excited to discuss the project.",
            "start_time": 3.5,
            "end_time": 7.8,
            "timestamp": "2025-01-15T10:30:00.000Z"
        }
    ],
    "refined_segments": [
        {
            "id": 1,
            "session_id": 1,
            "refined_speaker_id": 1,
            "text": "Hello everyone, welcome to our meeting today. We have a lot to discuss.",
            "start_time": 0.0,
            "end_time": 3.2,
            "confidence_score": 0.95,
            "source_segments": "[1]",
            "metadata": '{"processing_time": 1.2, "model_version": "gpt-4"}',
            "last_update": "2025-01-15T10:30:00.000Z",
            "is_processing": 0
        }
    ],
    "segment_usage": [
        {
            "raw_segment_id": 1,
            "refined_segment_id": 1,
            "timestamp": "2025-01-15T10:30:00.000Z"
        }
    ]
}

# Sample configuration data
SAMPLE_CONFIGURATION = {
    "database": {
        "path": ":memory:",
        "timeout": 5.0,
        "environment": "test"
    },
    "logging": {
        "level": "DEBUG",
        "format": "text",
        "file": "test.log"
    },
    "api": {
        "max_request_size_mb": 10,
        "max_json_size_mb": 5,
        "rate_limit_per_minute": 100
    },
    "openai": {
        "model": "gpt-4",
        "max_tokens": 2000,
        "temperature": 0.7
    },
    "transcript_refiner": {
        "min_segments_for_diarization": 4,
        "inactivity_seconds": 120,
        "confidence_threshold": 0.8
    }
}

# Sample test scenarios
TEST_SCENARIOS = {
    "basic_conversation": {
        "description": "Basic two-person conversation",
        "data": SAMPLE_SESSION_DATA,
        "expected_segments": 5,
        "expected_speakers": 3
    },
    "meeting_scenario": {
        "description": "Team meeting with multiple speakers",
        "data": SAMPLE_MEETING_DATA,
        "expected_segments": 11,
        "expected_speakers": 4
    },
    "interview_scenario": {
        "description": "Job interview conversation",
        "data": SAMPLE_INTERVIEW_DATA,
        "expected_segments": 10,
        "expected_speakers": 2
    },
    "error_scenarios": {
        "invalid_json": {
            "description": "Invalid JSON payload",
            "data": "invalid json",
            "expected_status": 400
        },
        "missing_session_id": {
            "description": "Missing session_id field",
            "data": {"segments": [], "log_timestamp": "2025-01-15T10:30:00.000Z"},
            "expected_status": 422
        },
        "empty_segments": {
            "description": "Empty segments array",
            "data": {"session_id": "test", "segments": [], "log_timestamp": "2025-01-15T10:30:00.000Z"},
            "expected_status": 422
        }
    }
}

# Performance test data
PERFORMANCE_TEST_DATA = {
    "small_dataset": {
        "sessions": 10,
        "segments_per_session": 5,
        "expected_processing_time": 2.0
    },
    "medium_dataset": {
        "sessions": 50,
        "segments_per_session": 10,
        "expected_processing_time": 10.0
    },
    "large_dataset": {
        "sessions": 100,
        "segments_per_session": 20,
        "expected_processing_time": 30.0
    }
}

# Load test data
LOAD_TEST_DATA = {
    "light_load": {
        "concurrent_requests": 10,
        "requests_per_second": 5,
        "duration_seconds": 60
    },
    "medium_load": {
        "concurrent_requests": 50,
        "requests_per_second": 25,
        "duration_seconds": 120
    },
    "heavy_load": {
        "concurrent_requests": 100,
        "requests_per_second": 50,
        "duration_seconds": 300
    }
}

# Security test data
SECURITY_TEST_DATA = {
    "sql_injection_attempts": [
        "'; DROP TABLE sessions; --",
        "1' OR '1'='1",
        "'; INSERT INTO sessions VALUES ('hacked', 'hacked'); --"
    ],
    "xss_attempts": [
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "<img src=x onerror=alert('xss')>"
    ],
    "path_traversal_attempts": [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "/etc/shadow"
    ]
}

# Utility functions for test data
def get_sample_data(data_type: str) -> Dict[str, Any]:
    """Get sample data by type."""
    data_map = {
        "session": SAMPLE_SESSION_DATA,
        "meeting": SAMPLE_MEETING_DATA,
        "interview": SAMPLE_INTERVIEW_DATA,
        "speakers": SAMPLE_SPEAKERS,
        "refined_segments": SAMPLE_REFINED_SEGMENTS,
        "error_responses": SAMPLE_ERROR_RESPONSES,
        "success_responses": SAMPLE_SUCCESS_RESPONSES,
        "openai_responses": SAMPLE_OPENAI_RESPONSES,
        "database_records": SAMPLE_DATABASE_RECORDS,
        "configuration": SAMPLE_CONFIGURATION
    }
    return data_map.get(data_type, {})


def create_test_session_data(session_id: str = None, segment_count: int = 5) -> Dict[str, Any]:
    """Create test session data with specified parameters."""
    if session_id is None:
        session_id = f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    segments = []
    current_time = 0.0
    
    for i in range(segment_count):
        speaker_id = (i % 4) + 1
        text = f"Test segment {i+1} for session {session_id}"
        duration = 2.0 + (i * 0.5)
        
        segments.append({
            "speaker_id": speaker_id,
            "text": text,
            "start_time": current_time,
            "end_time": current_time + duration
        })
        
        current_time += duration + 0.5
    
    return {
        "session_id": session_id,
        "log_timestamp": datetime.now(UTC).isoformat() + "Z",
        "segments": segments
    }


def create_malformed_data() -> List[Dict[str, Any]]:
    """Create various types of malformed data for error testing."""
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


def save_test_data_to_file(data: Dict[str, Any], filename: str) -> str:
    """Save test data to a JSON file."""
    filepath = os.path.join("tmp", filename)
    os.makedirs("tmp", exist_ok=True)
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    return filepath


def load_test_data_from_file(filename: str) -> Dict[str, Any]:
    """Load test data from a JSON file."""
    filepath = os.path.join("tmp", filename)
    
    with open(filepath, 'r') as f:
        return json.load(f)
