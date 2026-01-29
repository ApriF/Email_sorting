import sqlite3
import logging
from datetime import datetime
from pathlib import Path


class EmailDatabase:
    """Manages SQLite database for storing email data."""
    
    def __init__(self, db_path="output/emails.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self._init_database()
        logging.info(f"Database initialized: {self.db_path}")
    
    def _init_database(self):
        """Create database tables if they don't exist."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        
        cursor = self.conn.cursor()
        
        # Emails table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                sender TEXT,
                subject TEXT,
                date TEXT,
                category TEXT,
                has_attachments INTEGER DEFAULT 0,
                attachment_count INTEGER DEFAULT 0,
                body TEXT,
                error TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Attachments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id INTEGER,
                filename TEXT,
                file_path TEXT,
                category TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (email_id) REFERENCES emails(id)
            )
        """)
        
        # Create indexes for better query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON emails(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON emails(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_id ON attachments(email_id)")
        
        self.conn.commit()
    
    def insert_email(self, email_data, category, has_attachments=False, error=None):
        """Insert email record into database."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO emails (
                timestamp, sender, subject, date, category,
                has_attachments, attachment_count, body, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            email_data.get('sender', ''),
            email_data.get('subject', ''),
            email_data.get('date', ''),
            category,
            1 if has_attachments else 0,
            len(email_data.get('attachments', [])),
            email_data.get('body', ''),
            error or ''
        ))
        
        email_id = cursor.lastrowid
        self.conn.commit()
        return email_id
    
    def insert_attachment(self, email_id, filename, file_path, category):
        """Insert attachment record into database."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO attachments (email_id, filename, file_path, category)
            VALUES (?, ?, ?, ?)
        """, (email_id, filename, file_path, category))
        
        self.conn.commit()
    
    def get_emails_by_category(self, category):
        """Get all emails in a specific category."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM emails WHERE category = ?", (category,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self):
        """Get category statistics from database."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                category,
                COUNT(*) as count,
                SUM(has_attachments) as attachment_count
            FROM emails
            WHERE error = '' OR error IS NULL
            GROUP BY category
            ORDER BY count DESC
        """)
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_total_count(self):
        """Get total number of processed emails."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM emails")
        return cursor.fetchone()['total']
    
    def get_error_count(self):
        """Get number of emails with errors."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM emails WHERE error != '' AND error IS NOT NULL")
        return cursor.fetchone()['total']
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logging.info("Database connection closed")
