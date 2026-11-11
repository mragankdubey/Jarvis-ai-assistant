"""
Comprehensive Phase 4 Test Suite for J.A.R.V.I.S.

Tests:
1. SQLite database schema and CRUD repositories (Conversations, Memory, Notes, Reminders, Settings).
2. Configuration DB override persistence.
3. Subsystem diagnostics module (non-fabricated real probes).
4. Multi-resolution Arc Reactor Windows ICO generation.
5. Reimagined PySide6 HUD widgets, multi-screen switching, CRUD wiring, and clean shutdown.
"""

import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.assistant import Assistant
from core.config import Config
from core.diagnostics import check_network, check_wake_word_engine, get_system_telemetry
from core.states import AssistantState
from database.db import DatabaseManager
from database.models import JarvisRepository


class TestPhase4DatabaseAndPersistence(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmp.name) / "test_jarvis.db"
        self.db = DatabaseManager(self.db_path)
        self.repo = JarvisRepository(self.db)

    def tearDown(self):
        self._tmp.cleanup()

    def test_01_conversation_persistence(self):
        self.repo.add_message("user", "Hello JARVIS")
        self.repo.add_message("assistant", "At your service, sir.")
        msgs = self.repo.get_recent_messages(limit=10)
        self.assertEqual(len(msgs), 2)
        self.assertEqual(msgs[0].role, "user")
        self.assertEqual(msgs[1].content, "At your service, sir.")
        self.repo.clear_messages()
        self.assertEqual(len(self.repo.get_recent_messages()), 0)

    def test_02_memory_facts_crud(self):
        fid = self.repo.add_fact("Uses Python 3.12", "project")
        self.assertIsNotNone(fid)
        facts = self.repo.list_facts()
        self.assertEqual(len(facts), 1)
        self.assertEqual(facts[0].category, "project")
        self.assertEqual(len(self.repo.list_facts("Python")), 1)
        self.assertEqual(len(self.repo.list_facts("Rust")), 0)
        self.repo.delete_fact(facts[0].id)
        self.assertEqual(len(self.repo.list_facts()), 0)

    def test_03_notes_crud(self):
        nid = self.repo.create_note("Design Spec", "Arc reactor HUD")
        self.assertGreater(nid, 0)
        self.repo.update_note(nid, "Design Spec v2", "Updated HUD notes")
        notes = self.repo.list_notes("Updated")
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0].title, "Design Spec v2")
        self.repo.delete_note(nid)
        self.assertEqual(len(self.repo.list_notes()), 0)

    def test_04_reminders_and_due_check(self):
        rid = self.repo.add_reminder("Check telemetry", "2020-01-01 09:00")
        due = self.repo.get_due_unnotified_reminders("2026-11-10 12:00")
        self.assertEqual(len(due), 1)
        self.repo.mark_reminder_notified(rid)
        self.assertEqual(len(self.repo.get_due_unnotified_reminders("2026-11-10 12:00")), 0)
        self.repo.set_reminder_status(rid, "completed")
        self.assertEqual(self.repo.list_reminders("completed")[0].status, "completed")
        self.repo.delete_reminder(rid)
        self.assertEqual(len(self.repo.list_reminders()), 0)

    def test_05_config_db_override_roundtrip(self):
        cfg = Config(user_name="Tony", voice_rate=210, voice_enabled=False, accent_intensity=70)
        cfg.save_overrides(self.repo)

        loaded = Config()
        loaded.load_overrides(self.repo)
        self.assertEqual(loaded.user_name, "Tony")
        self.assertEqual(loaded.voice_rate, 210)
        self.assertFalse(loaded.voice_enabled)
        self.assertEqual(loaded.accent_intensity, 70)


class TestPhase4DiagnosticsAndIcons(unittest.TestCase):

    def test_06_system_telemetry_and_diagnostics(self):
        tel = get_system_telemetry()
        self.assertIn("cpu_percent", tel)
        self.assertIn("ram_percent", tel)
        self.assertIn("os", tel)

        ww_ok, ww_msg = check_wake_word_engine("hey_jarvis")
        self.assertTrue(ww_ok)
        self.assertIn("hey_jarvis", ww_msg)

        net_ok, net_msg = check_network()
        self.assertIsInstance(net_ok, bool)
        self.assertIsInstance(net_msg, str)

    def test_07_multi_res_ico_valid(self):
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(["-platform", "offscreen"])
        from interface.icon_generator import ICO_PATH, PNG_PATH, save_multi_res_ico

        save_multi_res_ico(ICO_PATH, PNG_PATH)
        self.assertTrue(ICO_PATH.exists())
        self.assertTrue(PNG_PATH.exists())

        data = ICO_PATH.read_bytes()
        reserved, img_type, count = struct.unpack("<HHH", data[:6])
        self.assertEqual(reserved, 0)
        self.assertEqual(img_type, 1)
        self.assertGreaterEqual(count, 6)


class TestPhase4HUDIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication(["-platform", "offscreen"])

    def test_08_hud_screens_and_crud_wiring(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = DatabaseManager(Path(tmp) / "hud_test.db")
            repo = JarvisRepository(db)
            cfg = Config.load(apply_db=False)
            assistant = Assistant(
                config=cfg,
                tts=MagicMock(),
                stt=MagicMock(),
                ai=MagicMock(),
                repo=repo,
            )

            from interface.main_window import MainWindow
            win = MainWindow(assistant=assistant, repo=repo, skip_startup=True)

            # Switch across all 7 screens cleanly
            for key in ("dashboard", "chat", "memory", "notes", "reminders", "system", "settings"):
                win.switch_screen(key, animate=False)
                self.app.processEvents()

            # Test memory add signal
            win.memory_screen.fact_added.emit("Prefers PySide6", "tech")
            self.assertEqual(len(repo.list_facts("PySide6")), 1)

            # Test notes save signal
            win.notes_screen.note_saved.emit(None, "HUD Test", "Testing note saving.")
            self.assertEqual(len(repo.list_notes("HUD Test")), 1)

            # Test reminder add signal
            win.reminders_screen.reminder_added.emit("Deploy build", "2026-12-01 10:00")
            self.assertEqual(len(repo.list_reminders("pending")), 1)

            # Test state propagation & waveform mic honesty
            win._apply_mic_status(False)
            label, _ = win.dashboard_screen.waveform._status_text()
            self.assertIn("MIC OFFLINE", label)

            win._handle_state_update(AssistantState.PROCESSING.value)
            self.assertIn("PROCESSING", win.state_pill.text())

            win._full_exit()


if __name__ == "__main__":
    unittest.main()
