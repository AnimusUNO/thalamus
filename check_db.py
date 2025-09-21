import sqlite3
from datetime import datetime

def check_db():
    conn = sqlite3.connect('thalamus.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    print("\n=== Sessions ===")
    cur.execute('SELECT * FROM sessions')
    sessions = cur.fetchall()
    for session in sessions:
        print(f"ID: {session['id']}, Session ID: {session['session_id']}, Created: {session['created_at']}")
    
    print("\n=== Speakers ===")
    cur.execute('SELECT * FROM speakers')
    speakers = cur.fetchall()
    for speaker in speakers:
        print(f"ID: {speaker['id']}, Name: {speaker['name']}, Created: {speaker['created_at']}")
    
    print("\n=== Raw Segments ===")
    cur.execute('''
        SELECT s.*, sp.name as speaker_name 
        FROM raw_segments s
        JOIN speakers sp ON s.speaker_id = sp.id
        ORDER BY s.timestamp
    ''')
    segments = cur.fetchall()
    for segment in segments:
        print(f"ID: {segment['id']}, Session: {segment['session_id']}, Speaker: {segment['speaker_name']}")
        print(f"Text: {segment['text']}")
        print(f"Time: {segment['start_time']} -> {segment['end_time']}")
        print(f"Timestamp: {segment['timestamp']}\n")
    
    print("\n=== Refined Segments ===")
    cur.execute('''
        SELECT * FROM refined_segments
        ORDER BY start_time, id
    ''')
    refined = cur.fetchall()
    for segment in refined:
        print(f"ID: {segment['id']}, Session: {segment['session_id']}, Speaker: {segment['refined_speaker_id']}")
        print(f"Text: {segment['text']}")
        print(f"Time: {segment['start_time']} -> {segment['end_time']}")
        print(f"Confidence: {segment['confidence_score']}")
        print(f"Source Segments: {segment['source_segments']}")
        print(f"Metadata: {segment['metadata']}\n")

if __name__ == '__main__':
    check_db() 