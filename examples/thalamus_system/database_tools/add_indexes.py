#!/usr/bin/env python3
"""
Thalamus Database Migration - Add Performance Indexes

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

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
from database import add_indexes_to_existing_db

def main():
    print("Adding performance indexes to existing database...")
    try:
        add_indexes_to_existing_db()
        print("✅ Performance indexes added successfully!")
        print("\nIndexes added:")
        print("- idx_raw_segments_session_id")
        print("- idx_raw_segments_timestamp") 
        print("- idx_raw_segments_speaker_id")
        print("- idx_refined_segments_session_id")
        print("- idx_refined_segments_start_time")
        print("- idx_refined_segments_last_update")
        print("- idx_segment_usage_refined_segment_id")
        print("- idx_segment_usage_timestamp")
        print("\nDatabase queries should now be significantly faster!")
    except Exception as e:
        print(f"❌ Error adding indexes: {e}")
        return 1
    return 0

if __name__ == '__main__':
    exit(main())
