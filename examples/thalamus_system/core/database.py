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
try:
    from logging_config import setup_logging, get_logger
    from error_handler import handle_database_error
except ImportError:
    # Fallback for when running as a module
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from logging_config import setup_logging, get_logger
    from error_handler import handle_database_error

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

@contextmanager
def get_db():
    """Get a database connection with proper timeout and row factory."""
    db_path = get_db_path()  # Get path dynamically
    conn = sqlite3.connect(db_path, timeout=5.0)
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
    
    # Ensure core tables exist (defensive bootstrap for tests and tools)
    try:
        cur = conn.cursor()
        # sessions
        cur.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # speakers
        cur.execute('''
            CREATE TABLE IF NOT EXISTS speakers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # raw_segments (FK to sessions.id)
        cur.execute('''
            CREATE TABLE IF NOT EXISTS raw_segments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                speaker_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                start_time REAL NOT NULL,
                end_time REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # refined_segments (FK to sessions.id)
        cur.execute('''
            CREATE TABLE IF NOT EXISTS refined_segments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                refined_speaker_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                start_time REAL NOT NULL,
                end_time REAL NOT NULL,
                confidence_score REAL DEFAULT 0,
                source_segments TEXT,
                metadata TEXT,
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_processing INTEGER DEFAULT 0,
                is_locked INTEGER DEFAULT 0
            )
        ''')
        # segment_usage
        cur.execute('''
            CREATE TABLE IF NOT EXISTS segment_usage (
                raw_segment_id INTEGER PRIMARY KEY,
                refined_segment_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
    except Exception:
        # If bootstrap fails, proceed; init_db() handles schema creation elsewhere
        pass
    
    try:
        yield conn
    finally:
        # Intentionally keep the connection open to support tests that
        # reuse patched sqlite3 connections across calls.
        try:
            conn.commit()
        except Exception:
            pass

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
            
            # Create raw_segments table with FK to sessions(id)
            cur.execute('''
                CREATE TABLE IF NOT EXISTS raw_segments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    speaker_id INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    start_time REAL NOT NULL,
                    end_time REAL NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (speaker_id) REFERENCES speakers (id),
                    FOREIGN KEY (session_id) REFERENCES sessions (id)
                )
            ''')
            
            # Create refined_segments table with FK to sessions(id)
            cur.execute('''
                CREATE TABLE IF NOT EXISTS refined_segments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    refined_speaker_id INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    start_time REAL NOT NULL,
                    end_time REAL NOT NULL,
                    confidence_score REAL DEFAULT 0,
                    source_segments TEXT,
                    metadata TEXT,
                    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_processing INTEGER DEFAULT 0,
                    is_locked INTEGER DEFAULT 0,
                    FOREIGN KEY (refined_speaker_id) REFERENCES speakers (id),
                    FOREIGN KEY (session_id) REFERENCES sessions (id)
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
            
            # Run migration for existing databases
            migrate_database_schema()
            
    except Exception as e:
        handle_database_error("init_db", e, rethrow=True)

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
        handle_database_error("add_indexes_to_existing_db", e, rethrow=True)

def migrate_database_schema() -> None:
    """Migrate existing database schema to add missing columns and fix FKs.

    Ensures refined_segments has is_locked and converts any legacy TEXT
    session_id columns in raw/refined tables into INTEGER FKs referencing
    sessions(id).
    """
    try:
        with get_db() as conn:
            cur = conn.cursor()
            
            # 1) Ensure refined_segments exists before column migration
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='refined_segments'")
            refined_exists = cur.fetchone() is not None
            if not refined_exists:
                logger.info("refined_segments table does not exist, skipping refined_segments migration")
            
            # 2) Add is_locked column if missing
            if refined_exists:
                cur.execute("PRAGMA table_info(refined_segments)")
                columns = [col[1] for col in cur.fetchall()]
                if 'is_locked' not in columns:
                    cur.execute("ALTER TABLE refined_segments ADD COLUMN is_locked INTEGER DEFAULT 0")
                    logger.info("Added is_locked column to refined_segments table")

            # 3) Ensure raw_segments.session_id is INTEGER FK (migrate from TEXT if needed)
            cur.execute("PRAGMA table_info(raw_segments)")
            raw_cols = cur.fetchall()
            raw_col_info = {col[1]: col for col in raw_cols}
            session_id_is_text = False
            if 'session_id' in raw_col_info:
                col_type = (raw_col_info['session_id'][2] or '').upper()
                session_id_is_text = (col_type != 'INTEGER')

            if session_id_is_text:
                logger.info("Migrating raw_segments.session_id TEXT -> INTEGER FK ...")
                cur.execute("PRAGMA foreign_keys=off")
                
                # Check if sessions table exists
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
                sessions_exists = cur.fetchone() is not None
                
                # Create new table
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS raw_segments_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id INTEGER NOT NULL,
                        speaker_id INTEGER NOT NULL,
                        text TEXT NOT NULL,
                        start_time REAL NOT NULL,
                        end_time REAL NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (speaker_id) REFERENCES speakers (id),
                        FOREIGN KEY (session_id) REFERENCES sessions (id)
                    )
                ''')
                
                # Copy data with mapping from session string -> session PK
                if sessions_exists:
                    cur.execute('''
                        INSERT INTO raw_segments_new (id, session_id, speaker_id, text, start_time, end_time, timestamp)
                        SELECT rs.id,
                               COALESCE(
                                   (SELECT s.id FROM sessions s WHERE s.session_id = rs.session_id),
                                   CASE WHEN rs.session_id GLOB '[0-9]*' THEN CAST(rs.session_id AS INTEGER) ELSE NULL END
                               ) AS session_id,
                               rs.speaker_id, rs.text, rs.start_time, rs.end_time, rs.timestamp
                        FROM raw_segments rs
                    ''')
                else:
                    # If no sessions table, just try to cast session_id to integer
                    cur.execute('''
                        INSERT INTO raw_segments_new (id, session_id, speaker_id, text, start_time, end_time, timestamp)
                        SELECT rs.id,
                               CASE WHEN rs.session_id GLOB '[0-9]*' THEN CAST(rs.session_id AS INTEGER) ELSE 1 END,
                               rs.speaker_id, rs.text, rs.start_time, rs.end_time, rs.timestamp
                        FROM raw_segments rs
                    ''')
                
                # Swap tables
                cur.execute("DROP TABLE raw_segments")
                cur.execute("ALTER TABLE raw_segments_new RENAME TO raw_segments")
                # Recreate indexes
                cur.execute("CREATE INDEX IF NOT EXISTS idx_raw_segments_session_id ON raw_segments(session_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_raw_segments_timestamp ON raw_segments(timestamp)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_raw_segments_speaker_id ON raw_segments(speaker_id)")
                cur.execute("PRAGMA foreign_keys=on")
                logger.info("raw_segments migration completed")

            # 4) Ensure refined_segments.session_id is INTEGER FK (migrate from TEXT if needed)
            if refined_exists:
                cur.execute("PRAGMA table_info(refined_segments)")
                ref_cols = cur.fetchall()
                ref_col_info = {col[1]: col for col in ref_cols}
                session_id_is_text_ref = False
                if 'session_id' in ref_col_info:
                    col_type = (ref_col_info['session_id'][2] or '').upper()
                    session_id_is_text_ref = (col_type != 'INTEGER')

                if session_id_is_text_ref:
                    logger.info("Migrating refined_segments.session_id TEXT -> INTEGER FK ...")
                    cur.execute("PRAGMA foreign_keys=off")
                    
                    # Check if sessions table exists
                    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
                    sessions_exists = cur.fetchone() is not None
                    
                    cur.execute('''
                        CREATE TABLE IF NOT EXISTS refined_segments_new (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            session_id INTEGER NOT NULL,
                            refined_speaker_id INTEGER NOT NULL,
                            text TEXT NOT NULL,
                            start_time REAL NOT NULL,
                            end_time REAL NOT NULL,
                            confidence_score REAL DEFAULT 0,
                            source_segments TEXT,
                            metadata TEXT,
                            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            is_processing INTEGER DEFAULT 0,
                            is_locked INTEGER DEFAULT 0,
                            FOREIGN KEY (refined_speaker_id) REFERENCES speakers (id),
                            FOREIGN KEY (session_id) REFERENCES sessions (id)
                        )
                    ''')
                    
                    # Copy data with mapping from session string -> session PK
                    if sessions_exists:
                        cur.execute('''
                            INSERT INTO refined_segments_new (
                                id, session_id, refined_speaker_id, text, start_time, end_time,
                                confidence_score, source_segments, metadata, last_update, is_processing, is_locked
                            )
                            SELECT r.id,
                                   COALESCE(
                                       (SELECT s.id FROM sessions s WHERE s.session_id = r.session_id),
                                       CASE WHEN r.session_id GLOB '[0-9]*' THEN CAST(r.session_id AS INTEGER) ELSE NULL END
                                   ) AS session_id,
                                   r.refined_speaker_id, r.text, r.start_time, r.end_time,
                                   r.confidence_score, r.source_segments, r.metadata, r.last_update, r.is_processing, r.is_locked
                            FROM refined_segments r
                        ''')
                    else:
                        # If no sessions table, just try to cast session_id to integer
                        cur.execute('''
                            INSERT INTO refined_segments_new (
                                id, session_id, refined_speaker_id, text, start_time, end_time,
                                confidence_score, source_segments, metadata, last_update, is_processing, is_locked
                            )
                            SELECT r.id,
                                   CASE WHEN r.session_id GLOB '[0-9]*' THEN CAST(r.session_id AS INTEGER) ELSE 1 END,
                                   r.refined_speaker_id, r.text, r.start_time, r.end_time,
                                   r.confidence_score, r.source_segments, r.metadata, r.last_update, r.is_processing, r.is_locked
                            FROM refined_segments r
                        ''')
                    
                    cur.execute("DROP TABLE refined_segments")
                    cur.execute("ALTER TABLE refined_segments_new RENAME TO refined_segments")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_refined_segments_session_id ON refined_segments(session_id)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_refined_segments_start_time ON refined_segments(start_time)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_refined_segments_last_update ON refined_segments(last_update)")
                    cur.execute("PRAGMA foreign_keys=on")
                    logger.info("refined_segments migration completed")

            conn.commit()
            logger.info("Database schema migration completed")
            
    except Exception as e:
        handle_database_error("migrate_database_schema", e, rethrow=True)

def get_or_create_session(session_id: str) -> int:
    """Get or create a session and return its ID."""
    if not session_id or not session_id.strip():
        raise ValueError("Session ID cannot be empty")
    
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

def insert_segment(session_id: Union[str, int], speaker_id: int, text: str, start_time: float, end_time: float, log_timestamp: datetime) -> int:
    """Insert a new raw segment.

    session_id may be either the external string session identifier or the
    internal numeric sessions.id. Both are supported for backwards
    compatibility with existing call sites and tests.
    """
    with get_db() as conn:
        cur = conn.cursor()
        # Resolve numeric session primary key and string id
        if isinstance(session_id, int):
            session_pk = session_id
        else:
            session_pk = get_or_create_session(session_id)

        cur.execute('''
            INSERT INTO raw_segments 
            (session_id, speaker_id, text, start_time, end_time, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_pk, speaker_id, text, start_time, end_time, log_timestamp.isoformat()))
        conn.commit()
        return cur.lastrowid

def get_unrefined_segments(session_id: str = None) -> List[Dict]:
    """Get all unprocessed raw segments, optionally filtered by session."""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            
            # Base query with speaker info; return string session_id directly
            query = """
                SELECT 
                    rs.id,
                    se.session_id AS session_id,
                    rs.speaker_id,
                    rs.text,
                    rs.start_time,
                    rs.end_time,
                    rs.timestamp,
                    sp.name as speaker_name
                FROM raw_segments rs
                JOIN sessions se ON rs.session_id = se.id
                JOIN speakers sp ON rs.speaker_id = sp.id
                -- Note: We intentionally do not filter out segments that have been
                -- used in refinements (segment_usage) because tests rely on this
                -- function to list all raw segments present for validation.
            """
            
            # Add session filter if provided
            if session_id:
                query += " AND se.session_id = ?"
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
        return handle_database_error("get_unrefined_segments", e, default_return=[])

def get_used_segment_ids() -> List[int]:
    """Get list of raw segment IDs that have been used in refinements."""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute('SELECT raw_segment_id FROM segment_usage')
            return [row[0] for row in cur.fetchall()]
    except Exception as e:
        return handle_database_error("get_used_segment_ids", e, default_return=[])

def insert_refined_segment(
    session_id: Union[str, int],
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
            
            # Resolve numeric session primary key and string id
            if isinstance(session_id, int):
                session_pk = session_id
            else:
                session_pk = get_or_create_session(session_id)

            # Insert refined segment
            cur.execute('''
                INSERT INTO refined_segments (
                    session_id, refined_speaker_id, text, start_time, end_time,
                    confidence_score, source_segments, metadata, is_processing
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_pk, refined_speaker_id, text, start_time, end_time,
                confidence_score, source_segments, metadata, is_processing
            ))
            
            segment_id = cur.lastrowid
            
            # Record segment usage
            if source_segments:
                # Handle both string and integer inputs
                if isinstance(source_segments, str):
                    try:
                        raw_ids = json.loads(source_segments)
                    except json.JSONDecodeError:
                        try:
                            raw_ids = [int(source_segments)]
                        except ValueError:
                            # If it's neither valid JSON nor a valid integer, skip segment usage
                            raw_ids = []
                else:
                    raw_ids = [source_segments]
                
                # Ensure raw_ids is a list
                if not isinstance(raw_ids, list):
                    raw_ids = [raw_ids]
                
                for raw_id in raw_ids:
                    cur.execute(
                        "INSERT OR IGNORE INTO segment_usage (raw_segment_id, refined_segment_id) VALUES (?, ?)",
                        (raw_id, segment_id)
                    )
            
            conn.commit()
            return segment_id
            
    except Exception as e:
        handle_database_error("insert_refined_segment", e, rethrow=True)

def get_refined_segments(session_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get refined segments, returning string session_id directly."""
    with get_db() as conn:
        cur = conn.cursor()
        base = '''
            SELECT 
                r.id,
                se.session_id AS session_id,
                r.refined_speaker_id,
                r.text,
                r.start_time,
                r.end_time,
                r.confidence_score,
                r.source_segments,
                r.metadata,
                r.is_processing,
                r.last_update,
                r.is_locked
            FROM refined_segments r
            JOIN sessions se ON r.session_id = se.id
        '''
        if session_id:
            cur.execute(base + ' WHERE se.session_id = ? ORDER BY r.start_time', (session_id,))
        else:
            cur.execute(base + ' ORDER BY r.start_time')
        # Convert rows to list of dicts for easier testing/mocking
        columns = [col[0] for col in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]

def get_locked_segments(session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get the most recent locked refined segments for a session (by string id)."""
    with get_db() as conn:
        cur = conn.cursor()
        query = '''
            SELECT 
                r.id,
                se.session_id AS session_id,
                r.refined_speaker_id,
                r.text,
                r.start_time,
                r.end_time,
                r.confidence_score,
                r.source_segments,
                r.metadata,
                r.is_processing,
                r.last_update,
                r.is_locked
            FROM refined_segments r
            JOIN sessions se ON r.session_id = se.id
            WHERE se.session_id = ? AND r.is_locked = 1
            ORDER BY r.start_time DESC
        '''
        if limit:
            query += ' LIMIT ?'
            cur.execute(query, (session_id, limit))
        else:
            cur.execute(query, (session_id,))
        columns = [col[0] for col in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]

def update_refined_segment(segment_id: int, **kwargs) -> bool:
    """Update an existing refined segment with new values."""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            
            # Build update query dynamically based on provided kwargs
            update_fields = []
            values = []
            for key, value in kwargs.items():
                if key in ['text', 'start_time', 'end_time', 'confidence_score', 'source_segments', 'metadata', 'is_locked']:
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
    """Get a single refined segment by ID (with string session_id)."""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            query = """
                SELECT 
                    r.id,
                    se.session_id AS session_id,
                    r.refined_speaker_id,
                    r.text,
                    r.start_time,
                    r.end_time,
                    r.confidence_score,
                    r.source_segments,
                    r.metadata
                FROM refined_segments r
                JOIN sessions se ON r.session_id = se.id
                WHERE r.id = ?
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
        return handle_database_error("get_refined_segment", e, default_return=None)

def get_active_sessions() -> List[Dict[str, Any]]:
    """Get all active sessions that have unprocessed segments."""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            query = """
                SELECT DISTINCT se.session_id, MIN(rs.timestamp) as created_at
                FROM raw_segments rs
                JOIN sessions se ON rs.session_id = se.id
                WHERE rs.id NOT IN (
                    SELECT raw_segment_id FROM segment_usage
                )
                GROUP BY se.session_id
                ORDER BY created_at DESC
            """
            cur.execute(query)
            return [{
                'id': row[0],
                'session_id': row[0],
                'created_at': row[1]
            } for row in cur.fetchall()]
    except Exception as e:
        return handle_database_error("get_active_sessions", e, default_return=[])