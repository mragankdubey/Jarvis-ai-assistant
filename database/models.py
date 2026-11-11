"""
Data Access Repositories and Models for J.A.R.V.I.S. SQLite Storage.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
from database.db import DatabaseManager, get_db


@dataclass
class MemoryFact:
    id: int
    category: str
    fact: str
    created_at: str


@dataclass
class NoteRecord:
    id: int
    title: str
    content: str
    file_path: Optional[str]
    updated_at: str


@dataclass
class ReminderRecord:
    id: int
    title: str
    due_at: str
    status: str
    notified: bool
    created_at: str


@dataclass
class ConversationRecord:
    id: int
    role: str
    content: str
    timestamp: str


class JarvisRepository:
    """Unified repository interface over J.A.R.V.I.S. SQLite tables."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or get_db()

    # --- Conversations ---
    def add_message(self, role: str, content: str) -> int:
        with self.db.connection() as conn:
            cur = conn.execute(
                "INSERT INTO conversations (role, content) VALUES (?, ?)",
                (role, content)
            )
            return int(cur.lastrowid or 0)

    def get_recent_messages(self, limit: int = 50) -> List[ConversationRecord]:
        with self.db.connection() as conn:
            rows = conn.execute(
                "SELECT id, role, content, timestamp FROM conversations ORDER BY id DESC LIMIT ?",
                (limit,)
            ).fetchall()
        return [
            ConversationRecord(r["id"], r["role"], r["content"], r["timestamp"])
            for r in reversed(rows)
        ]

    def clear_messages(self) -> None:
        with self.db.connection() as conn:
            conn.execute("DELETE FROM conversations")

    # --- Memory Facts ---
    def add_fact(self, fact: str, category: str = "general") -> Optional[int]:
        cleaned = fact.strip()
        if not cleaned:
            return None
        with self.db.connection() as conn:
            cur = conn.execute(
                "INSERT OR IGNORE INTO memory_facts (category, fact) VALUES (?, ?)",
                (category.strip() or "general", cleaned)
            )
            return int(cur.lastrowid) if cur.lastrowid else None

    def list_facts(self, query: str = "") -> List[MemoryFact]:
        with self.db.connection() as conn:
            if query.strip():
                like = f"%{query.strip()}%"
                rows = conn.execute(
                    "SELECT id, category, fact, created_at FROM memory_facts "
                    "WHERE fact LIKE ? OR category LIKE ? ORDER BY id DESC",
                    (like, like)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, category, fact, created_at FROM memory_facts ORDER BY id DESC"
                ).fetchall()
        return [MemoryFact(r["id"], r["category"], r["fact"], r["created_at"]) for r in rows]

    def delete_fact(self, fact_id: int) -> None:
        with self.db.connection() as conn:
            conn.execute("DELETE FROM memory_facts WHERE id = ?", (fact_id,))

    # --- Notes ---
    def create_note(self, title: str, content: str, file_path: Optional[str] = None) -> int:
        with self.db.connection() as conn:
            cur = conn.execute(
                "INSERT INTO notes (title, content, file_path) VALUES (?, ?, ?)",
                (title.strip() or "Untitled Note", content, file_path)
            )
            return int(cur.lastrowid or 0)

    def update_note(self, note_id: int, title: str, content: str) -> None:
        with self.db.connection() as conn:
            conn.execute(
                "UPDATE notes SET title = ?, content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (title.strip() or "Untitled Note", content, note_id)
            )

    def list_notes(self, query: str = "") -> List[NoteRecord]:
        with self.db.connection() as conn:
            if query.strip():
                like = f"%{query.strip()}%"
                rows = conn.execute(
                    "SELECT id, title, content, file_path, updated_at FROM notes "
                    "WHERE title LIKE ? OR content LIKE ? ORDER BY updated_at DESC, id DESC",
                    (like, like)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, title, content, file_path, updated_at FROM notes "
                    "ORDER BY updated_at DESC, id DESC"
                ).fetchall()
        return [
            NoteRecord(r["id"], r["title"], r["content"], r["file_path"], r["updated_at"])
            for r in rows
        ]

    def delete_note(self, note_id: int) -> None:
        with self.db.connection() as conn:
            conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))

    # --- Reminders ---
    def add_reminder(self, title: str, due_at: str) -> int:
        with self.db.connection() as conn:
            cur = conn.execute(
                "INSERT INTO reminders (title, due_at, status, notified) VALUES (?, ?, 'pending', 0)",
                (title.strip(), due_at.strip())
            )
            return int(cur.lastrowid or 0)

    def list_reminders(self, status: Optional[str] = None) -> List[ReminderRecord]:
        with self.db.connection() as conn:
            if status:
                rows = conn.execute(
                    "SELECT id, title, due_at, status, notified, created_at FROM reminders "
                    "WHERE status = ? ORDER BY due_at ASC, id DESC",
                    (status,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, title, due_at, status, notified, created_at FROM reminders "
                    "ORDER BY CASE WHEN status='pending' THEN 0 ELSE 1 END, due_at ASC, id DESC"
                ).fetchall()
        return [
            ReminderRecord(r["id"], r["title"], r["due_at"], r["status"], bool(r["notified"]), r["created_at"])
            for r in rows
        ]

    def set_reminder_status(self, reminder_id: int, status: str) -> None:
        with self.db.connection() as conn:
            conn.execute("UPDATE reminders SET status = ? WHERE id = ?", (status, reminder_id))

    def mark_reminder_notified(self, reminder_id: int) -> None:
        with self.db.connection() as conn:
            conn.execute("UPDATE reminders SET notified = 1 WHERE id = ?", (reminder_id,))

    def delete_reminder(self, reminder_id: int) -> None:
        with self.db.connection() as conn:
            conn.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))

    def get_due_unnotified_reminders(self, now_iso: Optional[str] = None) -> List[ReminderRecord]:
        check_time = now_iso or datetime.now().strftime("%Y-%m-%d %H:%M")
        with self.db.connection() as conn:
            rows = conn.execute(
                "SELECT id, title, due_at, status, notified, created_at FROM reminders "
                "WHERE status = 'pending' AND notified = 0 AND due_at <= ? ORDER BY due_at ASC",
                (check_time,)
            ).fetchall()
        return [
            ReminderRecord(r["id"], r["title"], r["due_at"], r["status"], bool(r["notified"]), r["created_at"])
            for r in rows
        ]

    # --- Settings ---
    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        with self.db.connection() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return str(row["value"]) if row else default

    def set_setting(self, key: str, value: str) -> None:
        with self.db.connection() as conn:
            conn.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, str(value))
            )

    def get_all_settings(self) -> Dict[str, str]:
        with self.db.connection() as conn:
            rows = conn.execute("SELECT key, value FROM settings").fetchall()
        return {str(r["key"]): str(r["value"]) for r in rows}

    def set_many_settings(self, values: Dict[str, str]) -> None:
        with self.db.connection() as conn:
            for k, v in values.items():
                conn.execute(
                    "INSERT INTO settings (key, value) VALUES (?, ?) "
                    "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                    (k, str(v))
                )
