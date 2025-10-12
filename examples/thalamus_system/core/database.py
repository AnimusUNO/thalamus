#!/usr/bin/env python3
"""
Thalamus Database Management

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

import sqlite3
from datetime import datetime
from contextlib import contextmanager
import json
from typing import List, Dict, Optional, Union, Any
from logging_config import setup_logging, get_logger

# Initialize centralized logging
setup_logging()
logger = get_logger(__name__)

import os
from pathlib import Path

# Configurable database path with environment-specific defaults
def get_db_path():
    """Get database path based on environment and configuration."""
    environment = os.getenv('ENVIRONMENT', 'development').lower()
    
    if environment == 'test':
        return ':memory:'  # In-memory database for testing
    elif environment == 'production':
        return os.getenv('THALAMUS_DB_PATH', '/var/lib/thalamus/thalamus.db')
    else:
        # Development - use env var or default to current location
        return os.getenv('THALAMUS_DB_PATH', 
                        str(Path(__file__).parent / 'thalamus.db'))

DB_PATH = get_db_path()

@contextmanager
def get_db():
    """Get a database connection with proper timeout and row factory."""
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    conn.row_factory = sqlite3.Row
    
    # Register JSON array contains function
    def json_array_contains(arr_str, value):
        """Check if a JSON array string contains a value."""
        try:
            if arr_str is None:
                return False
            arr = json.loads(arr_str)
            if not isinstance(arr, list):
                return False
            # Convert value to int since segment IDs are integers
            target = int(value)
            return target in [int(x) for x in arr]
        except:
            return False
    
    conn.create_function("json_array_contains", 2, json_array_contains)
    
    try:
        yield conn
    finally:
        conn.close()

def init_db() -> None:
    """Initialize the database with required tables."""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            
            # Create sessions table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create speakers table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS speakers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create raw_segments table
            cur.execute('''
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
            
            # Create refined_segments table
            cur.execute('''
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
            
            # Create segment_usage table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS segment_usage (
                    raw_segment_id INTEGER PRIMARY KEY,
                    refined_segment_id INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (refined_segment_id) REFERENCES refined_segments (id)
                )
            ''')
            
            # Add performance indexes for frequently queried columns
            indexes = [
                # Raw segments indexes
                "CREATE INDEX IF NOT EXISTS idx_raw_segments_session_id ON raw_segments(session_id)",
                "CREATE INDEX IF NOT EXISTS idx_raw_segments_timestamp ON raw_segments(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_raw_segments_speaker_id ON raw_segments(speaker_id)",
                
                # Refined segments indexes
                "CREATE INDEX IF NOT EXISTS idx_refined_segments_session_id ON refined_segments(session_id)",
                "CREATE INDEX IF NOT EXISTS idx_refined_segments_start_time ON refined_segments(start_time)",
                "CREATE INDEX IF NOT EXISTS idx_refined_segments_last_update ON refined_segments(last_update)",
                
                # Segment usage indexes
                "CREATE INDEX IF NOT EXISTS idx_segment_usage_refined_segment_id ON segment_usage(refined_segment_id)",
                "CREATE INDEX IF NOT EXISTS idx_segment_usage_timestamp ON segment_usage(timestamp)"
            ]
            
            for index_sql in indexes:
                cur.execute(index_sql)
            
            conn.commit()
            logger.info("Database initialized with tables and performance indexes")
            
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

def add_indexes_to_existing_db() -> None:
    """Add performance indexes to existing database (migration function)."""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            
            # Add performance indexes for frequently queried columns
            indexes = [
                # Raw segments indexes
                "CREATE INDEX IF NOT EXISTS idx_raw_segments_session_id ON raw_segments(session_id)",
                "CREATE INDEX IF NOT EXISTS idx_raw_segments_timestamp ON raw_segments(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_raw_segments_speaker_id ON raw_segments(speaker_id)",
                
                # Refined segments indexes
                "CREATE INDEX IF NOT EXISTS idx_refined_segments_session_id ON refined_segments(session_id)",
                "CREATE INDEX IF NOT EXISTS idx_refined_segments_start_time ON refined_segments(start_time)",
                "CREATE INDEX IF NOT EXISTS idx_refined_segments_last_update ON refined_segments(last_update)",
                
                # Segment usage indexes
                "CREATE INDEX IF NOT EXISTS idx_segment_usage_refined_segment_id ON segment_usage(refined_segment_id)",
                "CREATE INDEX IF NOT EXISTS idx_segment_usage_timestamp ON segment_usage(timestamp)"
            ]
            
            for index_sql in indexes:
                cur.execute(index_sql)
            
            conn.commit()
            logger.info("Performance indexes added to existing database")
            
    except Exception as e:
        logger.error(f"Error adding indexes to existing database: {e}")
        raise

def get_or_create_session(session_id: str) -> int:
    """Get or create a session and return its ID."""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('SELECT id FROM sessions WHERE session_id = ?', (session_id,))
        result = cur.fetchone()
        
        if result:
            return result['id']
        
        cur.execute('INSERT INTO sessions (session_id) VALUES (?)', (session_id,))
        conn.commit()
        return cur.lastrowid

def get_or_create_speaker(speaker_id: int, speaker_name: str, is_user: bool = False) -> int:
    """Get or create a speaker and return their ID."""
    with get_db() as conn:
        cur = conn.cursor()
        # First try to find by name
        cur.execute('SELECT id FROM speakers WHERE name = ?', (speaker_name,))
        result = cur.fetchone()
        
        if result:
            return result['id']
        
        # If not found, create new speaker
        cur.execute(
            'INSERT INTO speakers (name) VALUES (?)',
            (speaker_name,)
        )
        conn.commit()
        return cur.lastrowid

def insert_segment(session_id: int, speaker_id: int, text: str, start_time: float, end_time: float, log_timestamp: datetime) -> int:
    """Insert a new segment."""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO raw_segments 
            (session_id, speaker_id, text, start_time, end_time, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_id, speaker_id, text, start_time, end_time, log_timestamp))
        conn.commit()
        return cur.lastrowid

def get_unrefined_segments(session_id: str = None) -> List[Dict]:
    """Get all unprocessed raw segments, optionally filtered by session."""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            
            # Base query with speaker info
            query = """
                SELECT 
                    rs.id,
                    rs.session_id,
                    rs.speaker_id,
                    rs.text,
                    rs.start_time,
                    rs.end_time,
                    rs.timestamp,
                    s.name as speaker_name
                FROM raw_segments rs
                JOIN speakers s ON rs.speaker_id = s.id
                WHERE rs.id NOT IN (
                    SELECT raw_segment_id FROM segment_usage
                )
            """
            
            # Add session filter if provided
            if session_id:
                query += " AND rs.session_id = ?"
                logger.debug(f"Executing query: {query} with params: {session_id}")
                cur.execute(query, (session_id,))
            else:
                logger.debug(f"Executing query: {query}")
                cur.execute(query)
            
            # Convert to list of dicts
            columns = [col[0] for col in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]
            logger.debug(f"Query returned {len(results)} results")
            return results
            
    except Exception as e:
        logger.error(f"Error getting unrefined segments: {e}")
        return []

def get_used_segment_ids() -> List[int]:
    """Get list of raw segment IDs that have been used in refinements."""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute('SELECT raw_segment_id FROM segment_usage')
            return [row[0] for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error getting used segment IDs: {e}")
        return []

def insert_refined_segment(
    session_id: str,
    refined_speaker_id: int,
    text: str,
    start_time: float,
    end_time: float,
    confidence_score: float = 0,
    source_segments: str = None,
    metadata: str = None,
    is_processing: int = 0
) -> Optional[int]:
    """Insert a new refined segment and record segment usage."""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            
            # Insert refined segment
            cur.execute('''
                INSERT INTO refined_segments (
                    session_id, refined_speaker_id, text, start_time, end_time,
                    confidence_score, source_segments, metadata, is_processing
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id, refined_speaker_id, text, start_time, end_time,
                confidence_score, source_segments, metadata, is_processing
            ))
            
            segment_id = cur.lastrowid
            
            # Record segment usage
            if source_segments:
                for raw_id in json.loads(source_segments):
                    cur.execute(
                        "INSERT OR IGNORE INTO segment_usage (raw_segment_id, refined_segment_id) VALUES (?, ?)",
                        (raw_id, segment_id)
                    )
            
            conn.commit()
            return segment_id
            
    except Exception as e:
        logger.error(f"Error inserting refined segment: {e}")
        raise

def get_refined_segments(session_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get refined segments."""
    with get_db() as conn:
        cur = conn.cursor()
        if session_id:
            cur.execute('''
                SELECT * FROM refined_segments 
                WHERE session_id = ?
                ORDER BY start_time
            ''', (session_id,))
        else:
            cur.execute('SELECT * FROM refined_segments ORDER BY start_time')
        return cur.fetchall()

def get_locked_segments(session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get the most recent locked refined segments for a session."""
    with get_db() as conn:
        cur = conn.cursor()
        query = '''
            SELECT * FROM refined_segments 
            WHERE session_id = ? AND is_locked = 1
            ORDER BY start_time DESC
        '''
        if limit:
            query += ' LIMIT ?'
            cur.execute(query, (session_id, limit))
        else:
            cur.execute(query, (session_id,))
        return cur.fetchall()

def update_refined_segment(segment_id: int, **kwargs) -> bool:
    """Update an existing refined segment with new values."""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            
            # Build update query dynamically based on provided kwargs
            update_fields = []
            values = []
            for key, value in kwargs.items():
                if key in ['text', 'start_time', 'end_time', 'confidence_score', 'source_segments', 'metadata']:
                    update_fields.append(f"{key} = ?")
                    values.append(value)
            
            if not update_fields:
                return False
                
            # Add segment_id to values
            values.append(segment_id)
            
            # Execute update
            query = f"""
                UPDATE refined_segments 
                SET {', '.join(update_fields)}
                WHERE id = ?
            """
            cur.execute(query, values)
            conn.commit()
            
            return True
            
    except Exception as e:
        logger.error(f"Error updating refined segment {segment_id}: {e}")
        return False

def get_refined_segment(segment_id: int) -> Optional[Dict[str, Any]]:
    """Get a single refined segment by ID."""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            query = """
                SELECT 
                    id,
                    session_id,
                    refined_speaker_id,
                    text,
                    start_time,
                    end_time,
                    confidence_score,
                    source_segments,
                    metadata
                FROM refined_segments
                WHERE id = ?
            """
            cur.execute(query, (segment_id,))
            row = cur.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'session_id': row[1],
                    'refined_speaker_id': row[2],
                    'text': row[3],
                    'start_time': row[4],
                    'end_time': row[5],
                    'confidence_score': row[6],
                    'source_segments': row[7],
                    'metadata': row[8]
                }
            return None
            
    except Exception as e:
        logger.error(f"Error getting refined segment {segment_id}: {e}")
        return None

def get_active_sessions() -> List[Dict[str, Any]]:
    """Get all active sessions that have unprocessed segments."""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            query = """
                SELECT DISTINCT session_id, MIN(timestamp) as created_at
                FROM raw_segments
                WHERE id NOT IN (
                    SELECT raw_segment_id FROM segment_usage
                )
                GROUP BY session_id
                ORDER BY created_at DESC
            """
            cur.execute(query)
            return [{
                'id': row[0],  # Using session_id as id since we don't have a sessions table
                'session_id': row[0],
                'created_at': row[1]
            } for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error getting active sessions: {e}")
        return [] 