#!/usr/bin/env python3
"""
Thalamus Data Ingestion Application

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
from datetime import datetime, UTC
from typing import Dict, Any, List
from database import get_or_create_session, get_or_create_speaker, insert_segment
from logging_config import setup_logging, get_logger

# Initialize centralized logging
setup_logging()
logger = get_logger(__name__)

def process_event(event: Dict[str, Any]) -> None:
    """Process a single event and store it in the database."""
    try:
        # Get current event timestamp
        current_timestamp = datetime.fromisoformat(event['log_timestamp'].replace('Z', '+00:00'))
        logger.debug("Processing event at timestamp: %s", current_timestamp)
        
        # Get or create session
        session_id = event['session_id']
        db_session_id = get_or_create_session(session_id)
        logger.debug("Using database session ID: %d for session: %s", db_session_id, session_id)

        # Process segments
        for segment in event['segments']:
            try:
                # Get or create speaker
                speaker_id = int(segment['speaker_id'])  # Convert to integer
                db_speaker_id = get_or_create_speaker(
                    speaker_id=speaker_id,
                    speaker_name=segment['speaker'],
                    is_user=segment.get('is_user', False)
                )
                logger.debug("Using database speaker ID: %d for speaker: %s", db_speaker_id, segment['speaker'])

                # Insert segment into database
                segment_id = insert_segment(
                    session_id=db_session_id,
                    speaker_id=db_speaker_id,
                    text=segment['text'],
                    start_time=segment['start'],
                    end_time=segment['end'],
                    log_timestamp=current_timestamp
                )
                logger.info("Processed segment %d from %s: %s", 
                          segment_id, segment['speaker'], segment['text'][:50] + "...")
            except Exception as e:
                logger.error("Error processing segment: %s", e, exc_info=True)
                continue
                
    except Exception as e:
        logger.error("Error processing event: %s", e, exc_info=True)
        raise

def main() -> None:
    try:
        # Read events from file line by line
        import os
        data_file = os.path.join(os.path.dirname(__file__), 'raw_data_log.json')
        with open(data_file, 'r') as f:
            last_timestamp = None
            for line in f:
                event = json.loads(line)
                current_timestamp = datetime.fromisoformat(event['log_timestamp'].replace('Z', '+00:00'))
                
                # If we have a previous timestamp, wait the appropriate amount of time
                if last_timestamp:
                    time_diff = (current_timestamp - last_timestamp).total_seconds()
                    if time_diff > 0:
                        print(f"Waiting {time_diff:.2f} seconds to simulate real-time processing...")
                        time.sleep(time_diff)
                
                last_timestamp = current_timestamp
                
                # Process the event
                process_event(event)
    except Exception as e:
        print(f"Error processing events: {e}")

if __name__ == '__main__':
    main() 