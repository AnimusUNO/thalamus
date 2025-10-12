# Thalamus Demo Guide

*This documentation is licensed under [Creative Commons Attribution-ShareAlike 4.0 International](https://creativecommons.org/licenses/by-sa/4.0/) (CC BY-SA 4.0).*

## Overview

This guide explains how to run, improve, and observe the Thalamus demos. The system includes several demo components that showcase the real-time transcript refinement capabilities.

## Demo Components

### 1. Forensiq Demo (`examples/forensiq_demo/main.py`)
- **Purpose**: Interactive TUI demonstration of the cognitive architecture
- **Features**: Real-time visualization of Thalamus, Cerebellum, and Prime Agent
- **Interface**: Textual TUI with multiple panes showing data flow
- **Requirements**: `textual` and `rich` packages

### 2. Data Ingestion Demo (`thalamus_app.py`)
- **Purpose**: Simulates real-time speech-to-text data processing
- **Data Source**: `raw_data_log.json` (pre-recorded conversation)
- **Features**: Timestamp-based delays, session management, speaker tracking

### 3. Transcript Refinement Demo (`transcript_refiner.py`)
- **Purpose**: AI-powered transcript enhancement
- **Features**: Speaker grouping, context awareness, OpenAI integration
- **Output**: Refined, readable transcripts

### 4. Webhook Demo (`omi_webhook.py`)
- **Purpose**: Real-time webhook endpoint for live data
- **Features**: REST API, data validation, error handling

## Quick Start

### Prerequisites
```bash
# Ensure you have the required dependencies
pip install -r requirements.txt

# Set up environment variables
echo "OPENAI_API_KEY=your_api_key_here" > .env

# Navigate to examples directory
cd examples

# Initialize database
python init_db.py
```

### Running the Demos

#### Forensiq Demo (Recommended - Interactive TUI)
```bash
cd examples/forensiq_demo
pip install -r requirements.txt
python main.py
```
**What happens**: Interactive TUI showing the cognitive architecture in action

#### Complete System Demo (Multiple Terminals)

First, navigate to the examples directory:
```bash
cd examples
```

##### Terminal 1: Start Data Ingestion
```bash
python thalamus_app.py
```
**What happens**: Reads `raw_data_log.json` and processes events with real-time delays

##### Terminal 2: Start Transcript Refiner
```bash
python transcript_refiner.py
```
**What happens**: Continuously processes unrefined segments and creates enhanced transcripts

##### Terminal 3: Start Webhook Server (Optional)
```bash
python omi_webhook.py
```
**What happens**: Starts Flask server on `http://localhost:5000` for live webhook testing

## Demo Data Analysis

### Sample Data Structure (`examples/thalamus_system/thalamus_app/raw_data_log.json`)
The demo uses a 10-minute conversation with 4 speakers discussing technical topics:

```json
{
    "segments": [
        {
            "text": "Testing. Testing. Or do we have live connection?",
            "speaker": "SPEAKER_0",
            "speaker_id": 0,
            "is_user": false,
            "person_id": null,
            "start": 0.0,
            "end": 2.74
        }
    ],
    "session_id": "jTbLZFVyJjduPPvf0KQDqqPYhyU2",
    "log_timestamp": "2025-03-26T22:48:11.021743Z"
}
```

### Conversation Topics
- **Speaker 0**: Technical testing and system setup
- **Speaker 1**: Meeting coordination and timing
- **Speaker 2**: Process implementation and contracts
- **Speaker 3**: Technical documentation and procedures

## Observing the Demo

### 1. Real-Time Processing Observation

#### Data Ingestion (`thalamus_app.py`)
Watch for these log messages:
```
2025-01-01 12:00:00 - DEBUG - Processing event at timestamp: 2025-03-26T22:48:11.021743+00:00
2025-01-01 12:00:00 - INFO - Processed segment 1 from SPEAKER_0: Testing. Testing. Or do we have live connection?...
Waiting 0.90 seconds to simulate real-time processing...
```

#### Transcript Refinement (`transcript_refiner.py`)
Monitor the refinement process:
```
2025-01-01 12:00:01 - INFO - Processing 5 new segments for session jTbLZFVyJjduPPvf0KQDqqPYhyU2
2025-01-01 12:00:01 - INFO - Idle timeout flush for session jTbLZFVyJjduPPvf0KQDqqPYhyU2 after 120s inactivity
```

### 2. Database Monitoring

#### Check Database State
```bash
python check_db.py
```

**Expected Output**:
```
=== Sessions ===
ID: 1, Session ID: jTbLZFVyJjduPPvf0KQDqqPYhyU2, Created: 2025-01-01 12:00:00

=== Speakers ===
ID: 1, Name: SPEAKER_0, Created: 2025-01-01 12:00:00
ID: 2, Name: SPEAKER_1, Created: 2025-01-01 12:00:00
ID: 3, Name: SPEAKER_2, Created: 2025-01-01 12:00:00
ID: 4, Name: SPEAKER_3, Created: 2025-01-01 12:00:00

=== Raw Segments ===
ID: 1, Session: jTbLZFVyJjduPPvf0KQDqqPYhyU2, Speaker: SPEAKER_0
Text: Testing. Testing. Or do we have live connection?
Time: 0.0 -> 2.74
Timestamp: 2025-01-01 12:00:00

=== Refined Segments ===
ID: 1, Session: jTbLZFVyJjduPPvf0KQDqqPYhyU2, Speaker: 1
Text: Testing. Testing. Or do we have live connection?
Time: 0.0 -> 2.74
Confidence: 0.95
Source Segments: [1]
```

#### Audit Data Integrity
```bash
python audit_segment_usage.py
```

**Expected Output**:
```
Auditing segment integrity...

🔍 Unrefined Segment IDs: []
✅ Total Used Segment IDs: 264
✔️ No duplicate raw segments in refined data.
✔️ All unrefined segments are clean (not reused).
```

### 3. Webhook Testing

#### Test Ping Endpoint
```bash
curl http://localhost:5000/ping
# Expected: pong
```

#### Test Webhook with Sample Data
```bash
curl -X POST http://localhost:5000/omi \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo_test_123",
    "log_timestamp": "2025-01-01T12:00:00Z",
    "segments": [
      {
        "text": "This is a demo test message.",
        "speaker": "SPEAKER_0",
        "speaker_id": 0,
        "is_user": false,
        "person_id": null,
        "start": 0.0,
        "end": 3.0
      }
    ]
  }'
```

## Improving the Demos

### 1. Enhanced Data Ingestion Demo

#### Add Real-Time Webhook Integration
```python
# Enhanced thalamus_app.py
import requests
import threading
import time

def send_to_webhook(session_data):
    """Send processed data to webhook endpoint."""
    try:
        response = requests.post(
            'http://localhost:5000/omi',
            json=session_data,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        if response.status_code == 200:
            print(f"✅ Webhook sent successfully: {session_data['session_id']}")
        else:
            print(f"❌ Webhook failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Webhook error: {e}")

def process_event_with_webhook(event):
    """Process event and send to webhook."""
    # Process normally
    process_event(event)
    
    # Send to webhook in background
    threading.Thread(target=send_to_webhook, args=(event,)).start()
```

#### Add Progress Indicators
```python
def main():
    try:
        with open('raw_data_log.json', 'r') as f:
            lines = f.readlines()
            total_events = len(lines)
            
            for i, line in enumerate(lines, 1):
                event = json.loads(line)
                current_timestamp = datetime.fromisoformat(event['log_timestamp'].replace('Z', '+00:00'))
                
                # Show progress
                progress = (i / total_events) * 100
                print(f"📊 Progress: {progress:.1f}% ({i}/{total_events})")
                
                # Process with timing
                if last_timestamp:
                    time_diff = (current_timestamp - last_timestamp).total_seconds()
                    if time_diff > 0:
                        print(f"⏱️  Waiting {time_diff:.2f}s to simulate real-time...")
                        time.sleep(time_diff)
                
                process_event_with_webhook(event)
                last_timestamp = current_timestamp
                
    except Exception as e:
        print(f"❌ Error processing events: {e}")
```

### 2. Enhanced Transcript Refinement Demo

#### Add Real-Time Monitoring
```python
# Enhanced transcript_refiner.py
import time
from datetime import datetime

class EnhancedTranscriptRefiner(TranscriptRefiner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stats = {
            'segments_processed': 0,
            'sessions_active': 0,
            'start_time': datetime.now()
        }
    
    def process_session(self, session_id: str) -> bool:
        """Process session with enhanced monitoring."""
        start_time = time.time()
        result = super().process_session(session_id)
        processing_time = time.time() - start_time
        
        if result:
            self.stats['segments_processed'] += 1
            print(f"✅ Processed session {session_id} in {processing_time:.2f}s")
        
        return result
    
    def print_stats(self):
        """Print processing statistics."""
        runtime = (datetime.now() - self.stats['start_time']).total_seconds()
        rate = self.stats['segments_processed'] / runtime if runtime > 0 else 0
        
        print(f"📊 Stats: {self.stats['segments_processed']} segments, "
              f"{rate:.1f} segments/min, {self.stats['sessions_active']} active sessions")
    
    def run(self):
        """Enhanced main loop with monitoring."""
        print("🚀 Starting enhanced transcript refiner...")
        
        while True:
            try:
                # Process sessions
                sessions = get_active_sessions()
                self.stats['sessions_active'] = len(sessions)
                
                for session in sessions:
                    self.process_session(session['session_id'])
                
                # Flush idle sessions
                self.flush_idle_sessions()
                
                # Print stats every 30 seconds
                if int(time.time()) % 30 == 0:
                    self.print_stats()
                
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                time.sleep(5)
```

#### Add Quality Metrics
```python
def calculate_quality_metrics(session_id: str):
    """Calculate quality metrics for a session."""
    raw_segments = get_unrefined_segments(session_id)
    refined_segments = get_refined_segments(session_id)
    
    metrics = {
        'raw_count': len(raw_segments),
        'refined_count': len(refined_segments),
        'processing_rate': len(refined_segments) / len(raw_segments) if raw_segments else 0,
        'avg_confidence': sum(s['confidence_score'] for s in refined_segments) / len(refined_segments) if refined_segments else 0
    }
    
    return metrics
```

### 3. Enhanced Webhook Demo

#### Add Request Logging
```python
# Enhanced omi_webhook.py
import logging
from datetime import datetime

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('omi_webhook.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@app.route("/omi", methods=["POST"])
def omi_webhook():
    """Enhanced webhook with detailed logging."""
    start_time = datetime.now()
    client_ip = request.remote_addr
    
    try:
        data = request.get_json(force=True)
        session_id = data.get('session_id', 'unknown')
        segment_count = len(data.get('segments', []))
        
        logger.info(f"📥 Webhook received from {client_ip}: session={session_id}, segments={segment_count}")
        
        # Process data
        process_webhook_event(data)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ Webhook processed successfully: session={session_id}, time={processing_time:.2f}s")
        
        return jsonify({
            "status": "success",
            "session_id": session_id,
            "processing_time": processing_time,
            "segments_processed": segment_count
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "processing_time": (datetime.now() - start_time).total_seconds()
        }), 400
```

#### Add Health Dashboard
```python
@app.route("/dashboard", methods=["GET"])
def dashboard():
    """Simple health dashboard."""
    try:
        # Get system stats
        from database import get_active_sessions, get_refined_segments
        
        sessions = get_active_sessions()
        refined_segments = get_refined_segments()
        
        dashboard_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "active_sessions": len(sessions),
            "total_refined_segments": len(refined_segments),
            "uptime": (datetime.now() - start_time).total_seconds()
        }
        
        return jsonify(dashboard_data), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
```

## Demo Scenarios

### Scenario 1: Basic Processing Demo
```bash
# Terminal 1: Start data ingestion
python thalamus_app.py

# Terminal 2: Start refinement
python transcript_refiner.py

# Terminal 3: Monitor database
watch -n 5 "python check_db.py | head -20"
```

### Scenario 2: Webhook Integration Demo
```bash
# Terminal 1: Start webhook server
python omi_webhook.py

# Terminal 2: Start refinement
python transcript_refiner.py

# Terminal 3: Send test data
curl -X POST http://localhost:5000/omi \
  -H "Content-Type: application/json" \
  -d @sample_webhook_data.json
```

### Scenario 3: Performance Testing Demo
```bash
# Terminal 1: Start all services
python omi_webhook.py &
python transcript_refiner.py &

# Terminal 2: Run load test
python load_test.py

# Terminal 3: Monitor performance
python performance_monitor.py
```

## Custom Demo Data

### Creating Custom Test Data
```python
# create_demo_data.py
import json
import random
from datetime import datetime, timedelta

def create_demo_conversation():
    """Create a custom demo conversation."""
    speakers = ["SPEAKER_0", "SPEAKER_1", "SPEAKER_2"]
    topics = [
        "Hello, how are you today?",
        "I'm doing well, thank you for asking.",
        "What are we discussing in this meeting?",
        "We need to review the quarterly results.",
        "I have some questions about the budget.",
        "Let's go through each item one by one."
    ]
    
    session_id = f"demo_session_{int(datetime.now().timestamp())}"
    start_time = datetime.now()
    
    events = []
    current_time = start_time
    
    for i in range(20):  # 20 segments
        speaker = random.choice(speakers)
        speaker_id = speakers.index(speaker)
        text = random.choice(topics)
        
        # Random timing
        start_offset = random.uniform(0, 10)
        duration = random.uniform(1, 5)
        
        event = {
            "session_id": session_id,
            "log_timestamp": current_time.isoformat() + "Z",
            "segments": [
                {
                    "text": text,
                    "speaker": speaker,
                    "speaker_id": speaker_id,
                    "is_user": speaker_id == 0,
                    "person_id": None,
                    "start": start_offset,
                    "end": start_offset + duration
                }
            ]
        }
        
        events.append(event)
        current_time += timedelta(seconds=random.uniform(1, 5))
    
    return events

# Save demo data
events = create_demo_conversation()
with open('custom_demo_data.json', 'w') as f:
    for event in events:
        f.write(json.dumps(event) + '\n')

print(f"Created {len(events)} demo events")
```

### Running Custom Demo
```bash
# Create custom data
python create_demo_data.py

# Run with custom data
python thalamus_app.py custom_demo_data.json
```

## Troubleshooting Demos

### Common Issues

1. **Database Locked**
   ```bash
   # Solution: Reset database
   refresh.bat
   python init_db.py
   ```

2. **OpenAI API Errors**
   ```bash
   # Check API key
   echo $OPENAI_API_KEY
   
   # Test API connection
   python -c "from openai_wrapper import call_openai_text; print(call_openai_text('test'))"
   ```

3. **Port Already in Use**
   ```bash
   # Find and kill process
   netstat -ano | findstr :5000
   taskkill /PID <PID> /F
   ```

4. **Memory Issues**
   ```bash
   # Monitor memory usage
   python -c "import psutil; print(f'Memory: {psutil.virtual_memory().percent}%')"
   ```

### Debug Mode
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Run with debug output
python thalamus_app.py --debug
python transcript_refiner.py --debug
python omi_webhook.py --debug
```

## Demo Metrics

### Key Performance Indicators
- **Processing Rate**: Segments processed per minute
- **Latency**: Time from raw segment to refined segment
- **Accuracy**: Confidence scores of refined segments
- **Throughput**: Total segments processed per session
- **Error Rate**: Failed processing attempts

### Monitoring Script
```python
# monitor_demo.py
import time
import sqlite3
from datetime import datetime

def monitor_demo():
    """Monitor demo performance in real-time."""
    while True:
        try:
            conn = sqlite3.connect('thalamus.db')
            cursor = conn.cursor()
            
            # Get stats
            cursor.execute("SELECT COUNT(*) FROM raw_segments")
            raw_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM refined_segments")
            refined_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(confidence_score) FROM refined_segments")
            avg_confidence = cursor.fetchone()[0] or 0
            
            conn.close()
            
            # Print stats
            print(f"📊 {datetime.now().strftime('%H:%M:%S')} - "
                  f"Raw: {raw_count}, Refined: {refined_count}, "
                  f"Confidence: {avg_confidence:.2f}")
            
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    monitor_demo()
```

## Best Practices for Demos

1. **Start Simple**: Begin with basic functionality before adding complexity
2. **Monitor Performance**: Always track processing rates and errors
3. **Use Real Data**: Test with realistic conversation data
4. **Document Results**: Keep track of demo outcomes and metrics
5. **Prepare Fallbacks**: Have backup plans for common issues
6. **Test Edge Cases**: Try different scenarios and data formats
7. **Keep Logs**: Maintain detailed logs for troubleshooting
8. **Validate Output**: Always verify the quality of refined transcripts

This demo guide provides everything needed to run, improve, and observe the Thalamus system in action. Follow the scenarios and best practices to create compelling demonstrations of the transcript refinement capabilities.
