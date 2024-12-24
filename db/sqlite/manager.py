import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import uuid4

class SessionManager:
    def __init__(self, db_path='sessions.db'):
        """
        Initialize SQLite database for session management
        
        Args:
            db_path (str): Path to SQLite database file
        """
        self.db_path = db_path
        self._create_tables()

    def _get_connection(self):
        """Create a new database connection"""
        return sqlite3.connect(self.db_path)

    def _create_tables(self):
        """Create necessary tables for session management"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    end_time DATETIME,
                    status TEXT DEFAULT 'active',
                    metadata TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS session_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    message_type TEXT,
                    content TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                )
            ''')
            conn.commit()

    def start_session(self, user_id: str, initial_metadata: Optional[Dict] = None) -> str:
        """
        Start a new session
        
        Args:
            user_id (str): User identifier
            initial_metadata (dict, optional): Initial session metadata
        
        Returns:
            str: Generated session ID
        """
        session_id = str(uuid4())
        metadata = json.dumps(initial_metadata or {})
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sessions 
                (session_id, user_id, start_time, status, metadata) 
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, user_id, datetime.now(), 'active', metadata))
            conn.commit()
        
        return session_id

    def update_session(self, session_id: str, metadata: Optional[Dict] = None):
        """
        Update session metadata
        
        Args:
            session_id (str): Session identifier
            metadata (dict, optional): Metadata to update
        """
        if metadata:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE sessions 
                    SET metadata = ? 
                    WHERE session_id = ?
                ''', (json.dumps(metadata), session_id))
                conn.commit()

    def log_message(self, session_id: str, message_type: str, content: Any):
        """
        Log a message to the current session
        
        Args:
            session_id (str): Session identifier
            message_type (str): Type of message (e.g., 'human', 'ai', 'system')
            content (Any): Message content
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO session_messages 
                (session_id, message_type, content) 
                VALUES (?, ?, ?)
            ''', (session_id, message_type, json.dumps(content)))
            conn.commit()

    def end_session(self, session_id: str, status: str = 'completed'):
        """
        End a session
        
        Args:
            session_id (str): Session identifier
            status (str, optional): Session status
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE sessions 
                SET end_time = ?, status = ? 
                WHERE session_id = ?
            ''', (datetime.now(), status, session_id))
            conn.commit()

    def get_session_messages(self, session_id: str) -> list:
        """
        Retrieve all messages for a session
        
        Args:
            session_id (str): Session identifier
        
        Returns:
            list: Session messages
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT message_type, content, timestamp 
                FROM session_messages 
                WHERE session_id = ? 
                ORDER BY timestamp
            ''', (session_id,))
            return [
                {
                    'type': row[0], 
                    'content': json.loads(row[1]), 
                    'timestamp': row[2]
                } for row in cursor.fetchall()
            ]

    def cleanup_old_sessions(self, days: int = 30):
        """
        Remove sessions older than specified days
        
        Args:
            days (int, optional): Number of days to retain sessions
        """
        cutoff = datetime.now().replace(day=datetime.now().day - days)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM sessions 
                WHERE end_time < ? OR (start_time < ? AND status = 'active')
            ''', (cutoff, cutoff))
            conn.commit()

# Global session manager instance
session_manager = SessionManager()