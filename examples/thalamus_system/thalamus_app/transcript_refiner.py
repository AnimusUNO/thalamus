#!/usr/bin/env python3
"""
Thalamus Transcript Refinement Engine

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
import time
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
from database import (
    get_unrefined_segments, insert_refined_segment,
    get_refined_segments, get_locked_segments, get_db,
    update_refined_segment, get_refined_segment, get_active_sessions,
    get_or_create_speaker
)
try:
    from openai_wrapper import call_openai_text
except ImportError:
    # Fallback for when running as a module
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from openai_wrapper import call_openai_text
import re
try:
    from logging_config import setup_logging, get_logger
except ImportError:
    # Fallback for when running as a module
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
    from logging_config import setup_logging, get_logger

# Initialize centralized logging
setup_logging()
logger = get_logger(__name__)

class TranscriptRefiner:
    def __init__(self, min_segments_for_diarization: int = 4, inactivity_seconds: int = 120) -> None:
        self.min_segments = min_segments_for_diarization
        self.sentence_endings = ['.', '!', '?', '...']
        self.inactivity_seconds = inactivity_seconds
        self.session_states = {}  # session_id -> { speaker_id, group, last_received }
        logger.info("TranscriptRefiner initialized with min_segments_for_diarization=%d, inactivity_seconds=%d", 
                   min_segments_for_diarization, inactivity_seconds)

    def process_session(self, session_id: str) -> bool:
        """Process new segments for a session while maintaining state."""
        try:
            # Get unrefined segments for this session
            segments = get_unrefined_segments(session_id)
            if not segments:
                return True
                
            logger.info(f"Processing {len(segments)} new segments for session {session_id}")
            
            # Sort segments by start time
            segments.sort(key=lambda x: x['start_time'])
            
            # Initialize or get existing session state
            if session_id not in self.session_states:
                self.session_states[session_id] = {
                    "speaker_id": None,
                    "group": [],
                    "last_received": datetime.utcnow()
                }
            
            state = self.session_states[session_id]
            
            for segment in segments:
                # Update last received time
                state["last_received"] = datetime.utcnow()
                
                # Check for speaker change
                if state["speaker_id"] is not None and segment['speaker_id'] != state["speaker_id"]:
                    # Finalize current group before starting new one
                    if state["group"]:
                        self._finalize_group(state["group"], session_id)
                        state["group"] = []
                
                # Update current speaker and add segment to group
                state["speaker_id"] = segment['speaker_id']
                state["group"].append(segment)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing session {session_id}: {e}")
            return False

    def _finalize_group(self, segments: List[Dict[str, Any]], session_id: str) -> None:
        """Finalize a group of segments from the same speaker."""
        if not segments:
            return
            
        # Get speaker info from first segment
        speaker_id = segments[0]['speaker_id']
        speaker_name = segments[0]['speaker_name']
        
        # Get or create speaker using the standalone function
        refined_speaker_id = get_or_create_speaker(speaker_id, speaker_name)
        
        # Get timing info
        start_time = min(s['start_time'] for s in segments)
        end_time = max(s['end_time'] for s in segments)
        
        # Combine text from all segments
        combined_text = " ".join(s['text'] for s in segments)
        
        # Get source segment IDs
        source_segments = [s['id'] for s in segments]
        
        # Insert refined segment
        insert_refined_segment(
            session_id=session_id,
            refined_speaker_id=refined_speaker_id,
            text=combined_text,
            start_time=start_time,
            end_time=end_time,
            source_segments=json.dumps(source_segments)
        )

    def flush_idle_sessions(self) -> None:
        """Flush any sessions that have been inactive for too long."""
        current_time = datetime.utcnow()
        for session_id, state in list(self.session_states.items()):
            idle_duration = (current_time - state["last_received"]).total_seconds()
            if idle_duration >= self.inactivity_seconds and state["group"]:
                logger.info(f"Idle timeout flush for session {session_id} after {idle_duration}s inactivity")
                self._finalize_group(state["group"], session_id)
                del self.session_states[session_id]

    def run(self) -> None:
        """Main processing loop."""
        logger.info("Starting transcript refiner...")
        
        while True:
            try:
                # Get all active sessions
                sessions = get_active_sessions()
                
                for session in sessions:
                    session_id = session['session_id']
                    
                    # Process any unprocessed segments while maintaining state
                    self.process_session(session_id)
                
                # Flush any idle sessions
                self.flush_idle_sessions()
                
                # Sleep briefly to prevent CPU spinning
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(5)  # Longer sleep on error

if __name__ == '__main__':
    refiner = TranscriptRefiner()
    refiner.run() 