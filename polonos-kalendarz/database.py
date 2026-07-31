import os
import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path=None):
        if db_path is None:
            config_dir = os.path.expanduser("~/.config/polonos-kalendarz")
            os.makedirs(config_dir, exist_ok=True)
            db_path = os.path.join(config_dir, "database.db")
        
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            # Accounts Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    email TEXT PRIMARY KEY,
                    refresh_token TEXT,
                    display_name TEXT,
                    is_demo INTEGER DEFAULT 0
                );
            """)
            # Calendars Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS calendars (
                    id TEXT PRIMARY KEY,
                    account_email TEXT,
                    summary TEXT,
                    color TEXT,
                    selected INTEGER DEFAULT 1,
                    FOREIGN KEY (account_email) REFERENCES accounts (email) ON DELETE CASCADE
                );
            """)
            # Events Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    calendar_id TEXT,
                    account_email TEXT,
                    summary TEXT,
                    description TEXT,
                    start_time TEXT, -- ISO 8601 format (YYYY-MM-DDTHH:MM:SS)
                    end_time TEXT,   -- ISO 8601 format
                    location TEXT,
                    is_all_day INTEGER DEFAULT 0,
                    FOREIGN KEY (calendar_id) REFERENCES calendars (id) ON DELETE CASCADE,
                    FOREIGN KEY (account_email) REFERENCES accounts (email) ON DELETE CASCADE
                );
            """)
            
            # Migration check for existing databases
            try:
                conn.execute("ALTER TABLE events ADD COLUMN is_all_day INTEGER DEFAULT 0;")
            except sqlite3.OperationalError:
                pass
            # Settings Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );
            """)
            conn.commit()

    # --- Account Operations ---
    def save_account(self, email, refresh_token, display_name, is_demo=0):
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO accounts (email, refresh_token, display_name, is_demo)
                VALUES (?, ?, ?, ?);
            """, (email, refresh_token, display_name, int(is_demo)))
            conn.commit()

    def get_accounts(self):
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM accounts;")
            return [dict(row) for row in cursor.fetchall()]

    def delete_account(self, email):
        with self._get_connection() as conn:
            # Foreign keys ON DELETE CASCADE will handle calendars and events
            conn.execute("DELETE FROM accounts WHERE email = ?;", (email,))
            conn.commit()

    # --- Calendar Operations ---
    def save_calendar(self, calendar_id, account_email, summary, color, selected=1):
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO calendars (id, account_email, summary, color, selected)
                VALUES (?, ?, ?, ?, COALESCE((SELECT selected FROM calendars WHERE id = ?), ?));
            """, (calendar_id, account_email, summary, color, calendar_id, int(selected)))
            conn.commit()

    def set_calendar_selected(self, calendar_id, selected):
        with self._get_connection() as conn:
            conn.execute("UPDATE calendars SET selected = ? WHERE id = ?;", (int(selected), calendar_id))
            conn.commit()

    def update_calendar_color(self, calendar_id, color):
        with self._get_connection() as conn:
            conn.execute("UPDATE calendars SET color = ? WHERE id = ?;", (color, calendar_id))
            conn.commit()

    def get_calendars(self, account_email=None):
        with self._get_connection() as conn:
            if account_email:
                cursor = conn.execute("SELECT * FROM calendars WHERE account_email = ?;", (account_email,))
            else:
                cursor = conn.execute("SELECT * FROM calendars;")
            return [dict(row) for row in cursor.fetchall()]

    # --- Event Operations ---
    def save_events(self, events_list):
        """
        events_list is a list of dicts:
        {id, calendar_id, account_email, summary, description, start_time, end_time, location, is_all_day}
        """
        with self._get_connection() as conn:
            for event in events_list:
                conn.execute("""
                    INSERT OR REPLACE INTO events (id, calendar_id, account_email, summary, description, start_time, end_time, location, is_all_day)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    event['id'],
                    event['calendar_id'],
                    event['account_email'],
                    event.get('summary', '(Brak tytułu)'),
                    event.get('description', ''),
                    event['start_time'],
                    event['end_time'],
                    event.get('location', ''),
                    int(event.get('is_all_day', 0))
                ))
            conn.commit()

    def clear_events_for_calendar(self, calendar_id):
        with self._get_connection() as conn:
            conn.execute("DELETE FROM events WHERE calendar_id = ?;", (calendar_id,))
            conn.commit()

    def get_events_for_range(self, start_iso, end_iso):
        """
        Fetches events from only selected calendars that overlap with the range [start_iso, end_iso].
        Times are strings in ISO format.
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT e.*, c.color as calendar_color, c.summary as calendar_name, a.display_name as account_name
                FROM events e
                JOIN calendars c ON e.calendar_id = c.id
                JOIN accounts a ON e.account_email = a.email
                WHERE c.selected = 1
                  AND e.start_time <= ?
                  AND e.end_time >= ?
                ORDER BY e.start_time ASC;
            """, (end_iso, start_iso))
            return [dict(row) for row in cursor.fetchall()]

    def get_upcoming_events(self, limit=10):
        """
        Fetches upcoming events starting from now from only selected calendars.
        """
        now_iso = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT e.*, c.color as calendar_color, c.summary as calendar_name, a.display_name as account_name
                FROM events e
                JOIN calendars c ON e.calendar_id = c.id
                JOIN accounts a ON e.account_email = a.email
                WHERE c.selected = 1
                  AND e.end_time >= ?
                ORDER BY e.start_time ASC
                LIMIT ?;
            """, (now_iso, limit))
            return [dict(row) for row in cursor.fetchall()]

    # --- Settings Operations ---
    def set_setting(self, key, value):
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO settings (key, value)
                VALUES (?, ?);
            """, (key, value))
            conn.commit()

    def get_setting(self, key, default=None):
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT value FROM settings WHERE key = ?;", (key,))
            row = cursor.fetchone()
            return row['value'] if row else default

