"""
Verification and Test Suite for J.A.R.V.I.S. Phase 2.

Tests:
1. Module imports
2. Configuration loading and secret protection
3. Asynchronous TTS queue and non-blocking speech
4. STT module initialization and graceful error handling
5. Browser command routing (using mock opener to avoid opening real tabs during tests)
6. NewsAPI handling for missing key and network failure
7. CommandRouter integration
"""

import os
import sys
import time
import unittest
from unittest.mock import MagicMock, patch

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.config import Config, get_config
from core.command_router import CommandRouter
from voice.text_to_speech import TextToSpeech, get_tts, shutdown as shutdown_tts
from voice.speech_recognition import SpeechRecognizer
from skills.base import BaseSkill, SkillResult
from skills.browser import BrowserSkill
from skills.news import NewsSkill


class TestPhase2(unittest.TestCase):

    def test_01_module_imports(self):
        """1. Verify that all Phase 2 modules import cleanly without errors."""
        import core
        import core.config
        import core.command_router
        import voice
        import voice.text_to_speech
        import voice.speech_recognition
        import skills
        import skills.base
        import skills.browser
        import skills.news
        self.assertTrue(True)

    def test_02_config_loading_and_secrecy(self):
        """2. Verify configuration loads without revealing secrets in repr or summary."""
        cfg = Config.load()
        self.assertIsInstance(cfg.user_name, str)
        self.assertIsInstance(cfg.voice_rate, int)
        self.assertIsInstance(cfg.voice_volume, float)

        summary = cfg.status_summary()
        self.assertIn("NewsAPI", summary)
        self.assertIn("Groq API", summary)
        self.assertIn("Gemini API", summary)
        # Verify that actual secret values are NOT in the summary
        if cfg.news_api_key:
            self.assertNotIn(cfg.news_api_key, summary.values())
            self.assertNotIn(cfg.news_api_key, repr(cfg))
        if cfg.groq_api_key:
            self.assertNotIn(cfg.groq_api_key, summary.values())
            self.assertNotIn(cfg.groq_api_key, repr(cfg))

    def test_03_tts_queue_and_async(self):
        """3. Test TTS with multiple consecutive queued messages and non-blocking execution."""
        tts = get_tts()
        start = time.time()
        # Queue multiple messages non-blocking
        tts.speak("Test message one.", block=False)
        tts.speak("Test message two.", block=False)
        queue_duration = time.time() - start

        # Non-blocking enqueue should be nearly instantaneous (< 0.5s)
        self.assertLess(queue_duration, 0.5)

        # Allow worker to start speaking, then test stop()
        time.sleep(0.3)
        tts.stop()
        time.sleep(0.2)

        # Verify blocking speech completes
        start_block = time.time()
        tts.speak("Short test.", block=True)
        block_duration = time.time() - start_block
        self.assertGreater(block_duration, 0.05)

    def test_04_stt_error_handling(self):
        """4. Test STT module initialization and graceful failure on invalid device."""
        stt = SpeechRecognizer()
        self.assertIsNotNone(stt.recognizer)

        # Mock sr.Microphone to simulate missing audio device
        with patch("speech_recognition.Microphone", side_effect=OSError("No Default Input Device Available")):
            calib_res = stt.calibrate(duration=0.1)
            self.assertFalse(calib_res)

            rec_res = stt.listen_and_recognize(timeout=0.1, phrase_time_limit=0.1)
            self.assertIsNone(rec_res)

    def test_05_browser_routing_mocked(self):
        """5. Test browser routing without popping open real windows."""
        mock_opener = MagicMock(return_value=True)
        skill = BrowserSkill(opener=mock_opener)

        # Test capability detection
        self.assertTrue(skill.can_handle("open google"))
        self.assertTrue(skill.can_handle("open youtube"))
        self.assertTrue(skill.can_handle("open whatsapp"))
        self.assertTrue(skill.can_handle("open github"))
        self.assertTrue(skill.can_handle("play iron man theme"))
        self.assertTrue(skill.can_handle("search youtube for interstellar ost"))
        self.assertFalse(skill.can_handle("tell me a joke"))

        # Test execution
        res1 = skill.execute("open google")
        self.assertTrue(res1.success)
        mock_opener.assert_called_with("https://www.google.com")

        res2 = skill.execute("open github")
        self.assertTrue(res2.success)
        mock_opener.assert_called_with("https://github.com/")

        res3 = skill.execute("play queen radio ga ga")
        self.assertTrue(res3.success)
        self.assertIn("queen+radio+ga+ga", mock_opener.call_args[0][0])

    def test_06_news_missing_key_and_network_error(self):
        """6. Test NewsSkill behavior with missing key and network failure."""
        # Case A: Missing key
        skill_no_key = NewsSkill(api_key=None)
        # Force config key to None for test
        with patch.object(NewsSkill, "api_key", None):
            res_no_key = skill_no_key.execute("news")
            self.assertFalse(res_no_key.success)
            self.assertIn("not configured", res_no_key.message)

        # Case B: Network failure
        skill_with_key = NewsSkill(api_key="mock_test_key_xyz")
        import requests
        with patch("requests.get", side_effect=requests.exceptions.ConnectionError("Simulated network down")):
            res_net_err = skill_with_key.execute("news")
            self.assertFalse(res_net_err.success)
            self.assertTrue("internet" in res_net_err.message.lower() or "connect" in res_net_err.message.lower())
            # Ensure fake key was never leaked in response message
            self.assertNotIn("mock_test_key_xyz", res_net_err.message)

    def test_07_command_router(self):
        """7. Test end-to-end routing with CommandRouter."""
        mock_opener = MagicMock(return_value=True)
        browser = BrowserSkill(opener=mock_opener)
        news = NewsSkill(api_key="mock_key")
        router = CommandRouter(skills=[browser, news])

        # Recognized browser command
        res_b = router.route("open youtube")
        self.assertTrue(res_b.success)
        self.assertIn("Opening YouTube", res_b.message)

        # Unrecognized command
        res_unknown = router.route("fly to mars")
        self.assertFalse(res_unknown.success)
        self.assertIn("don't know how to handle", res_unknown.message)

        # Empty command
        res_empty = router.route("   ")
        self.assertFalse(res_empty.success)


if __name__ == "__main__":
    try:
        unittest.main()
    finally:
        shutdown_tts()
