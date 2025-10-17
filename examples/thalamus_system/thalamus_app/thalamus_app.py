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
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
from database import get_or_create_session, get_or_create_speaker, insert_segment
from logging_config import setup_logging, get_logger

# Initialize centralized logging
setup_logging()
logger = get_logger(__name__)

def process_event(event: Dict[str, Any]) -> None:
    """Process a single event payload and store its segments in the database.

    The expected event format is:
    {
      "session_id": str,
      "log_timestamp": ISO-8601 string (may end with 'Z'),
      "segments": [
         {"speaker_id": int, "text": str, "start_time": float, "end_time": float, ...},
         ...
      ]
    }
    """
    try:
        # Parse event timestamp robustly (handles values ending with 'Z' or already offset-aware)
        ts_raw = event['log_timestamp']
        if isinstance(ts_raw, str):
            # Normalize forms like "+00:00Z" (some tests append 'Z' after isoformat())
            if ts_raw.endswith('+00:00Z'):
                ts_norm = ts_raw[:-1]  # drop trailing Z
            elif ts_raw.endswith('Z'):
                ts_norm = ts_raw.replace('Z', '+00:00')
            else:
                ts_norm = ts_raw
            current_timestamp = datetime.fromisoformat(ts_norm)
        else:
            current_timestamp = ts_raw
        logger.debug("Processing event at timestamp: %s", current_timestamp)

        # Ensure session exists and get numeric PK
        session_id_str = event['session_id']
        db_session_id = get_or_create_session(session_id_str)
        logger.debug("Using database session ID: %d for session: %s", db_session_id, session_id_str)

        # Process segments
        for segment in event['segments']:
            try:
                # Determine speaker name (fallback if not provided)
                speaker_id_value = int(segment.get('speaker_id'))
                speaker_name = segment.get('speaker') or f"Speaker {speaker_id_value}"
                db_speaker_id = get_or_create_speaker(
                    speaker_id=speaker_id_value,
                    speaker_name=speaker_name,
                    is_user=segment.get('is_user', False)
                )
                logger.debug("Using database speaker ID: %d for speaker: %s", db_speaker_id, speaker_name)

                # Insert raw segment using correct keys
                segment_id = insert_segment(
                    session_id=session_id_str,
                    speaker_id=db_speaker_id,
                    text=segment['text'],
                    start_time=float(segment['start_time']),
                    end_time=float(segment['end_time']),
                    log_timestamp=current_timestamp
                )
                logger.info(
                    "Processed segment %d (speaker %s): %s",
                    segment_id,
                    speaker_name,
                    (segment['text'][:50] + "...") if len(segment['text']) > 50 else segment['text']
                )
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