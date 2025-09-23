# Thalamus Technical Reference

*This documentation is licensed under [Creative Commons Attribution-ShareAlike 4.0 International](https://creativecommons.org/licenses/by-sa/4.0/) (CC BY-SA 4.0).*

This document provides technical implementation details for the Thalamus system.

## Database Schema

The application uses SQLite with the following tables:

### Sessions Table
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `session_id` (TEXT UNIQUE) - External session identifier
- `created_at` (TIMESTAMP) - Creation timestamp

### Speakers Table
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `name` (TEXT) - Speaker display name
- `created_at` (TIMESTAMP) - Creation timestamp

### Raw Segments Table
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `session_id` (TEXT) - Session reference
- `speaker_id` (INTEGER FOREIGN KEY) - Speaker reference
- `text` (TEXT) - Raw transcript text
- `start_time` (REAL) - Audio start time (seconds)
- `end_time` (REAL) - Audio end time (seconds)
- `timestamp` (TIMESTAMP) - Processing timestamp

### Refined Segments Table
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `session_id` (TEXT) - Session reference
- `refined_speaker_id` (INTEGER FOREIGN KEY) - Speaker reference
- `text` (TEXT) - Refined transcript text
- `start_time` (REAL) - Combined start time
- `end_time` (REAL) - Combined end time
- `confidence_score` (REAL) - AI confidence (0-1)
- `source_segments` (TEXT) - JSON array of raw segment IDs
- `metadata` (TEXT) - Additional data (JSON)
- `is_processing` (INTEGER) - Processing flag (0/1)
- `last_update` (TIMESTAMP) - Last modification time

### Segment Usage Table
- `raw_segment_id` (INTEGER PRIMARY KEY) - Raw segment reference
- `refined_segment_id` (INTEGER FOREIGN KEY) - Refined segment reference
- `timestamp` (TIMESTAMP) - Usage timestamp

## Installation

### Prerequisites
- Python 3.8+
- OpenAI API key

### Setup
1. Clone the repository:
```bash
git clone https://github.com/animusos/thalamus.git
cd thalamus
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r examples/requirements.txt
```

4. Set up environment variables:
```bash
# Create .env file with your OpenAI API key
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

5. Initialize the database:
```bash
cd examples
python init_db.py
```

## Usage

### Running the Examples

The Thalamus system is organized as a reference architecture with examples in the `examples/` folder.

#### Forensiq Demo (Recommended)
```bash
cd examples/forensiq_demo
pip install -r requirements.txt
python main.py
```

#### Complete System Demo
```bash
cd examples
```

1. Initialize the database:
```bash
python init_db.py
```

2. Start the main application:
```bash
python thalamus_app.py
```

3. Start the transcript refiner (in another terminal):
```bash
python transcript_refiner.py
```

4. Start the webhook server (optional, in another terminal):
```bash
python omi_webhook.py
```

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Database Management
- **Check database state**: `python examples/check_db.py`
- **Audit data integrity**: `python examples/audit_segment_usage.py`
- **Reset database**: `examples/refresh.bat` (Windows) or manually delete `thalamus.db`

## API Reference

### Core Functions

#### Database Operations
- `get_or_create_session(session_id: str) -> int`
- `get_or_create_speaker(speaker_id: int, speaker_name: str, is_user: bool = False) -> int`
- `insert_segment(session_id: int, speaker_id: int, text: str, start_time: float, end_time: float, log_timestamp: datetime) -> int`
- `get_unrefined_segments(session_id: str = None) -> List[Dict]`
- `insert_refined_segment(...) -> Optional[int]`
- `get_refined_segments(session_id: str = None) -> List[Dict]`

#### OpenAI Integration
- `call_openai_text(prompt: str) -> str`

### Data Formats

#### Input Event Format
```json
{
    "session_id": "unique_session_id",
    "log_timestamp": "2025-03-26T22:48:11.021743Z",
    "segments": [
        {
            "text": "Hello, this is a test.",
            "speaker": "SPEAKER_0",
            "speaker_id": 0,
            "is_user": false,
            "person_id": null,
            "start": 0.0,
            "end": 2.74
        }
    ]
}
```

#### Refined Segment Format
```json
{
    "id": 1,
    "session_id": "unique_session_id",
    "refined_speaker_id": 1,
    "text": "Hello, this is a test. How are you today?",
    "start_time": 0.0,
    "end_time": 5.0,
    "confidence_score": 0.95,
    "source_segments": "[1, 2, 3]",
    "metadata": "{\"model\": \"gpt-4\"}"
}
```

## License

MIT License - see LICENSE file for details
