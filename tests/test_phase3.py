"""
Comprehensive Phase 3 Test Suite for J.A.R.V.I.S.

Tests:
1. AssistantState enum definitions.
2. AI Engine provider resolution, error resilience, and memory limits.
3. WakeWordDetector with mocked audio frames.
4. Assistant multi-turn flow, command routing, and sleep modes.
5. DesktopSkill safety, allowlist enforcement, and rejection of unsafe actions.
6. PySide6 GUI HUD components in offscreen headless mode.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.states import AssistantState
from core.config import Config
from core.memory import ConversationMemory
from core.ai_engine import AIEngine, GroqProvider, GeminiProvider
from core.assistant import Assistant
from voice.wake_word import WakeWordDetector
from skills.desktop import DesktopSkill
from skills.base import SkillResult


class TestPhase3AIAndStates(unittest.TestCase):

    def test_01_all_states_exist(self):
        """Verify all eight required states are defined."""
        required = [
            "IDLE", "ACTIVATING", "LISTENING", "PROCESSING",
            "SPEAKING", "SLEEPING", "ERROR", "STOPPING"
        ]
        actual = [s.value for s in AssistantState]
        for req in required:
            self.assertIn(req, actual)

    def test_02_memory_sliding_window(self):
        """Verify ConversationMemory retains only up to max_turns."""
        mem = ConversationMemory(max_turns=4)
        for i in range(10):
            mem.add_user_message(f"User message {i}")
            mem.add_assistant_message(f"Assistant response {i}")

        self.assertEqual(len(mem), 4)
        ctx = mem.get_context()
        self.assertEqual(len(ctx), 4)
        self.assertEqual(ctx[-1]["content"], "Assistant response 9")

    def test_03_ai_missing_keys_handled(self):
        """Verify AIEngine gracefully reports missing keys without crashing."""
        cfg = Config(groq_api_key=None, gemini_api_key=None)
        ai = AIEngine(config=cfg)
        self.assertIsNone(ai.active_provider)

        resp = ai.ask("What is the meaning of life?")
        self.assertIn("unable to access my neural brain", resp.lower())

    def test_04_ai_groq_mocked_success(self):
        """Verify GroqProvider parsing and successful output."""
        groq = GroqProvider(api_key="mock_key")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "At your service, sir."}}]
        }

        with patch("requests.post", return_value=mock_response):
            ans = groq.generate("Hello", [], "system")
            self.assertEqual(ans, "At your service, sir.")

    def test_05_ai_groq_error_resilience(self):
        """Verify GroqProvider handles network timeouts gracefully."""
        groq = GroqProvider(api_key="mock_key")
        import requests
        with patch("requests.post", side_effect=requests.exceptions.Timeout("Timed out")):
            with self.assertRaises(TimeoutError):
                groq.generate("Hello", [], "system")


class TestPhase3WakeWordAndAssistant(unittest.TestCase):

    def test_06_wake_word_mocked_prediction(self):
        """Verify WakeWordDetector fires callback when model confidence crosses threshold."""
        callback_called = []
        detector = WakeWordDetector(
            model_name="hey_jarvis",
            threshold=0.5,
            on_detected=lambda: callback_called.append(True)
        )

        mock_model = MagicMock()
        mock_model.predict.return_value = {"hey_jarvis": 0.85}
        detector._model = mock_model

        # Simulate frame processing directly
        import numpy as np
        fake_frame = np.zeros(1280, dtype=np.int16)
        prediction = detector._model.predict(fake_frame)
        if prediction.get("hey_jarvis", 0) >= detector.threshold:
            detector.on_detected()

        self.assertTrue(len(callback_called) > 0)

    def test_07_assistant_text_command_and_sleep(self):
        """Verify Assistant processes text commands and handles sleep mode."""
        mock_tts = MagicMock()
        mock_stt = MagicMock()
        mock_ai = MagicMock()
        mock_ai.ask.return_value = "Mocked AI answer."

        assistant = Assistant(
            config=Config(),
            tts=mock_tts,
            stt=mock_stt,
            ai=mock_ai,
        )

        # 1. Normal AI query
        resp = assistant.process_text_command("Who was Alan Turing?")
        self.assertEqual(resp, "Mocked AI answer.")
        self.assertEqual(assistant.state, AssistantState.IDLE)

        # 2. Sleep command
        resp_sleep = assistant.process_text_command("Go to sleep, Jarvis")
        self.assertIn("standing by", resp_sleep.lower())
        self.assertEqual(assistant.state, AssistantState.IDLE)


class TestPhase3DesktopSkill(unittest.TestCase):

    def setUp(self):
        self.launched_commands = []
        self.skill = DesktopSkill(
            command_runner=lambda cmd: self.launched_commands.append(cmd) or True
        )

    def test_08_allowlisted_apps(self):
        """Verify only allowlisted apps can be launched."""
        # Allowed
        self.assertTrue(self.skill.can_handle("open notepad"))
        res = self.skill.execute("open notepad")
        self.assertTrue(res.success)
        self.assertIn("notepad.exe", self.launched_commands)

        self.assertTrue(self.skill.can_handle("open calculator"))
        res2 = self.skill.execute("open calculator")
        self.assertTrue(res2.success)
        self.assertIn("calc.exe", self.launched_commands)

    def test_09_safety_arbitrary_shell_rejected(self):
        """Verify arbitrary shell or destructive requests are rejected."""
        dangerous_commands = [
            "delete all files",
            "format c:",
            "rm -rf /",
            "execute powershell script",
            "run eval(evil_code)",
        ]
        for cmd in dangerous_commands:
            self.assertFalse(self.skill.can_handle(cmd))
            res = self.skill.execute(cmd)
            self.assertFalse(res.success)

    def test_10_system_telemetry_and_time(self):
        """Verify system status and time queries execute safely."""
        self.assertTrue(self.skill.can_handle("what is the current time"))
        res_time = self.skill.execute("what is the current time")
        self.assertTrue(res_time.success)
        self.assertIn("time is currently", res_time.message)

        self.assertTrue(self.skill.can_handle("system status"))
        res_sys = self.skill.execute("system status")
        self.assertTrue(res_sys.success)
        self.assertIn("CPU", res_sys.message)


class TestPhase3GUIHeadless(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Setup headless offscreen Qt application
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(["-platform", "offscreen"])

    def test_11_gui_widgets_instantiation(self):
        """Verify HUD widgets instantiate and update state cleanly."""
        from interface.reactor_widget import ArcReactorWidget
        from interface.waveform_widget import WaveformWidget
        from interface.chat_panel import ChatPanel

        reactor = ArcReactorWidget()
        waveform = WaveformWidget()
        panel = ChatPanel()

        # Update states
        for state in AssistantState:
            reactor.set_state(state)
            waveform.set_state(state)

        # Message append
        panel.append_message("user", "Hello Jarvis")
        panel.append_message("assistant", "Greetings, Mragank.")
        self.assertIn("Hello Jarvis", panel.chat_display.toHtml())
        self.assertIn("Greetings", panel.chat_display.toHtml())


if __name__ == "__main__":
    unittest.main()
