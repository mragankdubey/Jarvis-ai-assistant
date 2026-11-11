"""
Authoritative Resource and Persistent User-Data Path Resolver for J.A.R.V.I.S.

Distinguishes between:
1. Read-only bundled application resources (sys._MEIPASS when frozen, repo root in dev).
2. Persistent writable Windows user-data directory (%LOCALAPPDATA%\\JARVIS\\)
   housing the SQLite database, notes, rotating logs, backups, and user .env.
"""

import logging
import os
from pathlib import Path
import shutil
import sqlite3
import sys
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


def is_frozen() -> bool:
    """Return True when running inside a PyInstaller frozen executable."""
    return bool(getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"))


def get_resource_root() -> Path:
    """Return the root folder containing read-only bundled assets and code."""
    if is_frozen():
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent


def get_asset_path(*parts: str) -> Path:
    """Resolve a read-only asset path under assets/."""
    return get_resource_root().joinpath("assets", *parts)


def get_user_data_dir() -> Path:
    """
    Return the persistent writable Windows user-data directory (%LOCALAPPDATA%\\JARVIS).
    Respects JARVIS_DATA_DIR override for isolated testing.
    """
    override = os.getenv("JARVIS_DATA_DIR", "").strip()
    if override:
        base = Path(override)
    else:
        local_app_data = os.getenv("LOCALAPPDATA", "").strip()
        if local_app_data:
            base = Path(local_app_data) / "JARVIS"
        else:
            base = Path.home() / "AppData" / "Local" / "JARVIS"

    base.mkdir(parents=True, exist_ok=True)
    return base


def get_db_dir() -> Path:
    d = get_user_data_dir() / "database"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_db_path() -> Path:
    return get_db_dir() / "jarvis.db"


def get_notes_dir() -> Path:
    d = get_user_data_dir() / "notes"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_logs_dir() -> Path:
    d = get_user_data_dir() / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_backups_dir() -> Path:
    d = get_user_data_dir() / "backups"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_user_env_path() -> Path:
    return get_user_data_dir() / ".env"


def ensure_user_env_template() -> Path:
    """
    Ensure a safe, secret-free .env template guide exists in user-data dir
    if the user hasn't created .env yet. Never overwrites existing .env.
    """
    user_env = get_user_env_path()
    example_target = get_user_data_dir() / ".env.example"
    if not example_target.exists():
        bundled_example = get_resource_root() / ".env.example"
        if bundled_example.exists():
            try:
                shutil.copy2(bundled_example, example_target)
            except Exception as e:
                logger.debug("Could not copy .env.example template: %s", e)
    return user_env


def migrate_legacy_database() -> Optional[Path]:
    """
    On first run after moving to %LOCALAPPDATA%\\JARVIS, safely copy any existing
    development database (repo/database/jarvis.db) into the persistent location
    if the persistent database does not already exist. Never overwrites existing data.
    """
    target_db = get_db_path()
    if target_db.exists():
        return target_db

    if not is_frozen():
        legacy_db = Path(__file__).resolve().parent.parent / "database" / "jarvis.db"
        if legacy_db.exists() and legacy_db.resolve() != target_db.resolve():
            try:
                shutil.copy2(legacy_db, target_db)
                logger.info("Migrated legacy database from %s to %s", legacy_db, target_db)
                return target_db
            except Exception as e:
                logger.warning("Legacy database migration failed: %s", e)
    return None


def backup_database(db_path: Optional[Path] = None, keep_last: int = 5) -> Optional[Path]:
    """
    Create a safe online SQLite backup in %LOCALAPPDATA%\\JARVIS\\backups\\
    using SQLite's native backup API and prune older backups.
    """
    source = Path(db_path) if db_path else get_db_path()
    if not source.exists():
        return None

    backups_dir = get_backups_dir()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = backups_dir / f"jarvis_backup_{stamp}.db"

    try:
        src_conn = sqlite3.connect(str(source), timeout=5.0)
        dst_conn = sqlite3.connect(str(dest), timeout=5.0)
        try:
            src_conn.backup(dst_conn)
        finally:
            dst_conn.close()
            src_conn.close()

        # Prune older backups
        all_backups = sorted(backups_dir.glob("jarvis_backup_*.db"))
        if len(all_backups) > keep_last:
            for old in all_backups[:-keep_last]:
                try:
                    old.unlink()
                except Exception:
                    pass
        return dest
    except Exception as e:
        logger.warning("Database backup skipped: %s", e)
        return None
