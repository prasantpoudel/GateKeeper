import sqlite3
import time
from typing import Optional, Any
from .base import Storage


class SQLiteStorage(Storage):
    def __init__(self, db_path: str = "gatekeeper.db"):
        # check_same_thread=False allows using connection across threads
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._init_db()

    def _init_db(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS kv_store (
                key TEXT PRIMARY KEY,
                value TEXT,
                expiry REAL
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS timestamps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT,
                timestamp REAL,
                expiry REAL
            )
        """)
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_timestamps_key ON timestamps(key)"
        )
        self.conn.commit()

    def _cleanup_expired(self, key: str):
        now = time.time()
        self.cursor.execute(
            "DELETE FROM kv_store WHERE key = ? AND expiry IS NOT NULL AND expiry < ?",
            (key, now),
        )
        self.cursor.execute(
            "DELETE FROM timestamps WHERE key = ? AND expiry IS NOT NULL AND expiry < ?",
            (key, now),
        )
        self.conn.commit()

    def get(self, key: str) -> Optional[Any]:
        self._cleanup_expired(key)
        self.cursor.execute("SELECT value FROM kv_store WHERE key = ?", (key,))
        row = self.cursor.fetchone()
        return row[0] if row else None

    def set(self, key: str, value: Any, expiry: Optional[int] = None):
        exp_time = time.time() + expiry if expiry else None
        self.cursor.execute(
            "REPLACE INTO kv_store (key, value, expiry) VALUES (?, ?, ?)",
            (key, str(value), exp_time),
        )
        self.conn.commit()

    def incr(self, key: str, amount: int = 1, expiry: Optional[int] = None) -> int:
        self._cleanup_expired(key)

        self.cursor.execute("SELECT value, expiry FROM kv_store WHERE key = ?", (key,))
        row = self.cursor.fetchone()

        if row:
            val = int(row[0]) + amount
            current_expiry = row[1]
        else:
            val = amount
            current_expiry = None

        # Determine new expiry
        if expiry:
            new_expiry = time.time() + expiry
        else:
            new_expiry = current_expiry

        self.cursor.execute(
            "REPLACE INTO kv_store (key, value, expiry) VALUES (?, ?, ?)",
            (key, str(val), new_expiry),
        )
        self.conn.commit()
        return val

    def add_timestamp(self, key: str, timestamp: float, expiry: Optional[int] = None):
        # We don't strictly need to cleanup here but good practice
        # self._cleanup_expired(key)
        # Actually cleanup is expensive if done too often.
        # Maybe skip it on add? But then we accumulate garbage.
        # Let's keep it but maybe optimize later.

        exp_time = time.time() + expiry if expiry else None
        self.cursor.execute(
            "INSERT INTO timestamps (key, timestamp, expiry) VALUES (?, ?, ?)",
            (key, timestamp, exp_time),
        )
        self.conn.commit()

    def count_timestamps(self, key: str, start: float, end: float) -> int:
        self._cleanup_expired(key)
        self.cursor.execute(
            "SELECT COUNT(*) FROM timestamps WHERE key = ? AND timestamp BETWEEN ? AND ?",
            (key, start, end),
        )
        return self.cursor.fetchone()[0]

    def remove_timestamps(self, key: str, max_timestamp: float):
        # self._cleanup_expired(key) # Can skip here
        self.cursor.execute(
            "DELETE FROM timestamps WHERE key = ? AND timestamp <= ?",
            (key, max_timestamp),
        )
        self.conn.commit()
