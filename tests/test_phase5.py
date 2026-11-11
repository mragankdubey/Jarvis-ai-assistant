"""
Phase 5 Deployment, Persistence, Security & Packaging Verification Tests for J.A.R.V.I.S.
"""

import io
import logging
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core import paths
from core.config import Config
from core.logging_config import SecretMaskingFilter, _NullSafeStream
from database.db import DatabaseManager, get_db
from database.models import JarvisRepository


class TestPhase5PathsAndPersistence(unittest.TestCase):

    def test_01_persistent_user_data_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"JARVIS_DATA_DIR": tmp}):
                self.assertEqual(paths.get_user_data_dir(), Path(tmp))
                self.assertEqual(paths.get_db_path(), Path(tmp) / "database" / "jarvis.db")
                self.assertEqual(paths.get_notes_dir(), Path(tmp) / "notes")
                self.assertEqual(paths.get_logs_dir(), Path(tmp) / "logs")
                self.assertEqual(paths.get_backups_dir(), Path(tmp) / "backups")

    def test_02_frozen_resource_resolution(self):
        with tempfile.TemporaryDirectory() as fake_meipass:
            with patch.object(sys, "frozen", True, create=True), \
                 patch.object(sys, "_MEIPASS", fake_meipass, create=True):
                self.assertTrue(paths.is_frozen())
                self.assertEqual(paths.get_resource_root(), Path(fake_meipass))
                self.assertEqual(
                    paths.get_asset_path("icons", "jarvis.ico"),
                    Path(fake_meipass) / "assets" / "icons" / "jarvis.ico",
                )

    def test_03_first_run_db_and_non_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"JARVIS_DATA_DIR": tmp}):
                db1 = get_db()
                repo1 = JarvisRepository(db1)
                repo1.add_fact("Persistent Fact 123", "test")
                self.assertTrue(paths.get_db_path().exists())

                # Re-initialize DB manager at same path: data MUST remain preserved
                db2 = DatabaseManager()
                repo2 = JarvisRepository(db2)
                facts = repo2.list_facts("Persistent Fact 123")
                self.assertEqual(len(facts), 1)

    def test_04_database_backup_and_pruning(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"JARVIS_DATA_DIR": tmp}):
                db = DatabaseManager()
                repo = JarvisRepository(db)
                repo.create_note("Backup Note", "Important persistent content")
                backup = paths.backup_database(db.db_path, keep_last=2)
                self.assertIsNotNone(backup)
                self.assertTrue(backup.exists())

    def test_05_user_env_template_never_copies_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"JARVIS_DATA_DIR": tmp}):
                user_env = paths.ensure_user_env_template()
                example_copy = Path(tmp) / ".env.example"
                self.assertTrue(example_copy.exists())
                self.assertFalse(user_env.exists())

    def test_06_save_api_keys_to_user_env_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"JARVIS_DATA_DIR": tmp}, clear=False):
                cfg = Config()
                saved_path = cfg.save_api_keys_to_user_env(groq_key="gsk_test_dummy_123456")
                self.assertEqual(saved_path, Path(tmp) / ".env")
                self.assertTrue(saved_path.exists())
                # Repr and status_summary must still never reveal raw secret
                self.assertNotIn("gsk_test_dummy_123456", repr(cfg))
                self.assertNotIn("gsk_test_dummy_123456", str(cfg.status_summary()))


class TestPhase5LoggingAndSecurity(unittest.TestCase):

    def test_07_secret_redaction_filter(self):
        flt = SecretMaskingFilter(["my_custom_secret_token_99"])
        samples = [
            "Calling Groq with gsk_AbCdEfGhIjKlMnOpQrStUvWx",
            "Request failed: https://newsapi.org/v2/top?apiKey=fd3da075c9f74715&country=us",
            "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.fake",
            "Using key my_custom_secret_token_99",
        ]
        for msg in samples:
            rec = logging.LogRecord("test", logging.INFO, __file__, 1, msg, (), None)
            flt.filter(rec)
            self.assertNotIn("gsk_AbCdEfGhIjKlMnOpQrStUvWx", rec.msg)
            self.assertNotIn("fd3da075c9f74715", rec.msg)
            self.assertNotIn("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9", rec.msg)
            self.assertNotIn("my_custom_secret_token_99", rec.msg)
            self.assertIn("[REDACTED]", rec.msg)

    def test_08_null_safe_stdio_stream(self):
        stream = _NullSafeStream()
        self.assertEqual(stream.write("hello"), 5)
        stream.flush()
        self.assertFalse(stream.isatty())


class TestPhase5DeploymentArtifacts(unittest.TestCase):

    def test_09_packaging_files_and_spec_safety(self):
        root = Path(__file__).resolve().parent.parent
        for rel in (
            "JARVIS.spec",
            "version_info.txt",
            "build_windows.bat",
            "scripts/create_shortcuts.ps1",
            "installer/JARVIS.iss",
            "assets/icons/jarvis.ico",
            "assets/icons/jarvis.png",
        ):
            self.assertTrue((root / rel).exists(), f"Missing packaging artifact: {rel}")

        spec_text = (root / "JARVIS.spec").read_text(encoding="utf-8")
        # Ensure .env is never bundled directly in datas
        self.assertNotIn('".env")', spec_text)
        self.assertNotIn("'.env')", spec_text)
        self.assertIn("jarvis.ico", spec_text)
        self.assertIn("console=False", spec_text)


if __name__ == "__main__":
    unittest.main()
