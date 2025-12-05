"""
Event Database Module
SQLite database for logging detection events
"""
import sqlite3
import os
from datetime import datetime
import json


class EventDatabase:
    """Manages SQLite database for detection events"""
    
    def __init__(self, db_path='data/logs/events.db'):
        """
        Initialize event database
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        
        # Create directory if needed
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        print(f"🗄️ EventDatabase initialized: {db_path}")
    
    def _init_database(self):
        """Create tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Detection events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detection_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                zone_name TEXT,
                confidence REAL,
                bbox_x1 INTEGER,
                bbox_y1 INTEGER,
                bbox_x2 INTEGER,
                bbox_y2 INTEGER,
                recording_file TEXT,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # System events table (alerts, errors, status changes)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Statistics table (daily summaries)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                total_detections INTEGER DEFAULT 0,
                total_alerts INTEGER DEFAULT 0,
                total_recordings INTEGER DEFAULT 0,
                zones_triggered TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_detection_timestamp 
            ON detection_events(timestamp)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_detection_zone 
            ON detection_events(zone_name)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_system_timestamp 
            ON system_events(timestamp)
        ''')
        
        conn.commit()
        conn.close()
    
    def log_detection(self, zone_name=None, confidence=0.0, 
                     bbox=None, recording_file=None, metadata=None):
        """
        Log a person detection event
        
        Args:
            zone_name: Name of zone where detection occurred
            confidence: Detection confidence score
            bbox: Bounding box [x1, y1, x2, y2]
            recording_file: Path to associated recording
            metadata: Additional metadata as dict
        
        Returns:
            Event ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        # Parse bounding box (handle numpy arrays)
        if bbox is not None and len(bbox) == 4:
            x1, y1, x2, y2 = bbox
        else:
            x1, y1, x2, y2 = None, None, None, None
        
        # Convert metadata to JSON
        metadata_json = json.dumps(metadata) if metadata else None
        
        cursor.execute('''
            INSERT INTO detection_events 
            (timestamp, event_type, zone_name, confidence, 
             bbox_x1, bbox_y1, bbox_x2, bbox_y2, recording_file, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, 'person_detected', zone_name, confidence,
              x1, y1, x2, y2, recording_file, metadata_json))
        
        event_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return event_id
    
    def log_system_event(self, event_type, severity='info', 
                        message=None, metadata=None):
        """
        Log a system event (alert, error, status change)
        
        Args:
            event_type: Type of system event
            severity: Event severity (info, warning, error, critical)
            message: Human-readable message
            metadata: Additional metadata as dict
        
        Returns:
            Event ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        metadata_json = json.dumps(metadata) if metadata else None
        
        cursor.execute('''
            INSERT INTO system_events 
            (timestamp, event_type, severity, message, metadata)
            VALUES (?, ?, ?, ?, ?)
        ''', (timestamp, event_type, severity, message, metadata_json))
        
        event_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return event_id
    
    def update_daily_stats(self, date=None, detections=0, 
                          alerts=0, recordings=0, zones=None):
        """
        Update daily statistics
        
        Args:
            date: Date string (YYYY-MM-DD), defaults to today
            detections: Number of detections to add
            alerts: Number of alerts to add
            recordings: Number of recordings to add
            zones: List of zone names triggered
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        zones_json = json.dumps(zones) if zones else None
        
        cursor.execute('''
            INSERT INTO daily_stats 
            (date, total_detections, total_alerts, total_recordings, zones_triggered)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                total_detections = total_detections + ?,
                total_alerts = total_alerts + ?,
                total_recordings = total_recordings + ?,
                zones_triggered = ?,
                updated_at = CURRENT_TIMESTAMP
        ''', (date, detections, alerts, recordings, zones_json,
              detections, alerts, recordings, zones_json))
        
        conn.commit()
        conn.close()
    
    def get_recent_detections(self, limit=10, zone_name=None):
        """
        Get recent detection events
        
        Args:
            limit: Maximum number of events to return
            zone_name: Filter by zone (optional)
        
        Returns:
            List of detection events
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if zone_name:
            cursor.execute('''
                SELECT * FROM detection_events 
                WHERE zone_name = ?
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (zone_name, limit))
        else:
            cursor.execute('''
                SELECT * FROM detection_events 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        events = [dict(row) for row in rows]
        
        conn.close()
        return events
    
    def get_detections_by_timerange(self, start_time, end_time):
        """
        Get detections within time range
        
        Args:
            start_time: Start timestamp (ISO format)
            end_time: End timestamp (ISO format)
        
        Returns:
            List of detection events
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM detection_events 
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp ASC
        ''', (start_time, end_time))
        
        rows = cursor.fetchall()
        events = [dict(row) for row in rows]
        
        conn.close()
        return events
    
    def get_zone_statistics(self, days=7):
        """
        Get detection statistics by zone
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dict with zone statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                zone_name,
                COUNT(*) as detection_count,
                AVG(confidence) as avg_confidence,
                MAX(confidence) as max_confidence,
                MIN(timestamp) as first_detection,
                MAX(timestamp) as last_detection
            FROM detection_events 
            WHERE timestamp >= datetime('now', '-' || ? || ' days')
            GROUP BY zone_name
            ORDER BY detection_count DESC
        ''', (days,))
        
        rows = cursor.fetchall()
        stats = {}
        
        for row in rows:
            zone_name = row[0] if row[0] else 'unknown'
            stats[zone_name] = {
                'count': row[1],
                'avg_confidence': row[2],
                'max_confidence': row[3],
                'first_detection': row[4],
                'last_detection': row[5]
            }
        
        conn.close()
        return stats
    
    def get_daily_summary(self, date=None):
        """
        Get daily statistics summary
        
        Args:
            date: Date string (YYYY-MM-DD), defaults to today
        
        Returns:
            Dict with daily statistics
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM daily_stats 
            WHERE date = ?
        ''', (date,))
        
        row = cursor.fetchone()
        
        if row:
            summary = dict(row)
            if summary.get('zones_triggered'):
                summary['zones_triggered'] = json.loads(summary['zones_triggered'])
        else:
            summary = None
        
        conn.close()
        return summary
    
    def cleanup_old_events(self, days=30):
        """
        Delete events older than specified days
        
        Args:
            days: Number of days to keep
        
        Returns:
            Number of deleted events
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete old detection events
        cursor.execute('''
            DELETE FROM detection_events 
            WHERE timestamp < datetime('now', '-' || ? || ' days')
        ''', (days,))
        
        detections_deleted = cursor.rowcount
        
        # Delete old system events
        cursor.execute('''
            DELETE FROM system_events 
            WHERE timestamp < datetime('now', '-' || ? || ' days')
        ''', (days,))
        
        system_deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        total_deleted = detections_deleted + system_deleted
        
        if total_deleted > 0:
            print(f"🗑️ Database cleanup: Deleted {total_deleted} old events")
        
        return total_deleted
    
    def get_total_events(self):
        """Get total number of events in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM detection_events')
        detections = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM system_events')
        system = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'detections': detections,
            'system_events': system,
            'total': detections + system
        }
