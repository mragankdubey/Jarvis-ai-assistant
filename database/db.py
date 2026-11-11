"""
SQLite Database Manager for J.A.R.V.I.S.

Provides thread-safe connection management, schema initialization,
and automatic path setup under the project's data directory.
"""

from contextlib import contextmanager
import logging
from pathlib import Path
import sqlite3
import threading
from typing import Iterator, Optional
from core.paths import backup_database, get_db_path, migrate_legacy_database

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Thread-safe SQLite database wrapper and schema manager."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is not None:
            self.db_path = Path(db_path)
        else:
            migrate_legacy_database()
            self.db_path = get_db_path()
            if self.db_path.exists():
                backup_database(self.db_path)

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_schema()

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """Yield a thread-safe SQLite connection with row factory and automatic commit."""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path), timeout=10.0)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def _init_schema(self) -> None:
        """Create required application tables if they do not exist."""
        with self.connection() as conn:
            cursor = conn.cursor()

            # 1. Conversation History
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 2. Persistent Memory Facts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory_facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL DEFAULT 'general',
                    fact TEXT NOT NULL UNIQUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 3. Notes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    file_path TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 4. Reminders & Tasks
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    due_at TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    notified INTEGER NOT NULL DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 5. User Preferences / Settings
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

        logger.info("SQLite database initialized at %s", self.db_path)


_db_instance: Optional[DatabaseManager] = None
_db_lock = threading.Lock()


def get_db(db_path: Optional[Path] = None) -> DatabaseManager:
    """Get or create singleton DatabaseManager."""
    global _db_instance
    with _db_lock:
        if db_path is not None:
            _db_instance = DatabaseManager(db_path=db_path)
        elif _db_instance is None or _db_instance.db_path != get_db_path():
            _db_instance = DatabaseManager(db_path=None)
        return _db_instance
