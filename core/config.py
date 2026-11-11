"""
Configuration Management Module for J.A.R.V.I.S.

Loads settings from environment variables, .env file, and persisted SQLite preferences.
Never exposes secret values in logs or representations.
"""

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv

# Ensure .env is loaded from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH)


@dataclass
class Config:
    """Holds configuration parameters for J.A.R.V.I.S."""

    # User and assistant identity
    user_name: str = "Mragank"
    assistant_name: str = "JARVIS"

    # AI Brain Provider ('auto', 'groq', 'gemini')
    ai_provider: str = "auto"

    # API credentials (optional)
    news_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None

    # Voice TTS settings
    voice_enabled: bool = True
    voice_rate: int = 180
    voice_volume: float = 1.0

    # Speech Recognition settings
    stt_timeout: float = 5.0
    stt_phrase_time_limit: float = 8.0
    stt_ambient_duration: float = 1.0

    # Wake Word settings
    wake_word_enabled: bool = True
    wake_word_model: str = "hey_jarvis"
    wake_word_threshold: float = 0.5
    inactivity_timeout: float = 10.0  # seconds of silence before returning to IDLE

    # Desktop HUD preferences
    minimize_to_tray: bool = True
    startup_animation: bool = True
    accent_intensity: int = 85  # 30 - 100

    @classmethod
    def load(cls, apply_db: bool = True) -> "Config":
        """Load and return configuration from environment variables and optionally SQLite settings."""
        news_key = os.getenv("NEWS_API_KEY") or os.getenv("newsapi_key") or None
        if news_key:
            news_key = news_key.strip().strip('"').strip("'")

        groq_key = os.getenv("GROQ_API_KEY") or None
        if groq_key:
            groq_key = groq_key.strip().strip('"').strip("'")

        gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or None
        if gemini_key:
            gemini_key = gemini_key.strip().strip('"').strip("'")

        raw_rate = os.getenv("JARVIS_VOICE_RATE", "180")
        try:
            voice_rate = int(raw_rate)
        except ValueError:
            voice_rate = 180

        raw_volume = os.getenv("JARVIS_VOICE_VOLUME", "1.0")
        try:
            voice_volume = max(0.0, min(1.0, float(raw_volume)))
        except ValueError:
            voice_volume = 1.0

        user_name = os.getenv("JARVIS_USER_NAME", "Mragank").strip() or "Mragank"
        ai_provider = os.getenv("AI_PROVIDER", "auto").strip().lower()

        try:
            inactivity = float(os.getenv("JARVIS_INACTIVITY_TIMEOUT", "10.0"))
        except ValueError:
            inactivity = 10.0

        try:
            wake_threshold = float(os.getenv("JARVIS_WAKE_THRESHOLD", "0.5"))
        except ValueError:
            wake_threshold = 0.5

        cfg = cls(
            user_name=user_name,
            ai_provider=ai_provider,
            news_api_key=news_key,
            groq_api_key=groq_key,
            gemini_api_key=gemini_key,
            voice_rate=voice_rate,
            voice_volume=voice_volume,
            wake_word_threshold=wake_threshold,
            inactivity_timeout=inactivity,
        )

        if apply_db:
            try:
                from database.models import JarvisRepository
                cfg.load_overrides(JarvisRepository())
            except Exception:
                pass

        return cfg

    def load_overrides(self, repo: Any) -> None:
        """Apply persisted non-secret user preferences from SQLite repository."""
        saved = repo.get_all_settings()
        if not saved:
            return
        if "user_name" in saved and saved["user_name"].strip():
            self.user_name = saved["user_name"].strip()
        if "ai_provider" in saved:
            self.ai_provider = saved["ai_provider"].lower()
        if "voice_enabled" in saved:
            self.voice_enabled = saved["voice_enabled"].lower() == "true"
        if "wake_word_enabled" in saved:
            self.wake_word_enabled = saved["wake_word_enabled"].lower() == "true"
        if "minimize_to_tray" in saved:
            self.minimize_to_tray = saved["minimize_to_tray"].lower() == "true"
        if "startup_animation" in saved:
            self.startup_animation = saved["startup_animation"].lower() == "true"
        if "voice_rate" in saved:
            try:
                self.voice_rate = max(100, min(300, int(saved["voice_rate"])))
            except ValueError:
                pass
        if "voice_volume" in saved:
            try:
                self.voice_volume = max(0.0, min(1.0, float(saved["voice_volume"])))
            except ValueError:
                pass
        if "inactivity_timeout" in saved:
            try:
                self.inactivity_timeout = max(3.0, min(60.0, float(saved["inactivity_timeout"])))
            except ValueError:
                pass
        if "wake_word_threshold" in saved:
            try:
                self.wake_word_threshold = max(0.2, min(0.95, float(saved["wake_word_threshold"])))
            except ValueError:
                pass
        if "accent_intensity" in saved:
            try:
                self.accent_intensity = max(30, min(100, int(saved["accent_intensity"])))
            except ValueError:
                pass

    def save_overrides(self, repo: Any) -> None:
        """Persist non-secret user preferences into SQLite repository."""
        repo.set_many_settings({
            "user_name": self.user_name,
            "ai_provider": self.ai_provider,
            "voice_enabled": str(self.voice_enabled).lower(),
            "wake_word_enabled": str(self.wake_word_enabled).lower(),
            "minimize_to_tray": str(self.minimize_to_tray).lower(),
            "startup_animation": str(self.startup_animation).lower(),
            "voice_rate": str(self.voice_rate),
            "voice_volume": f"{self.voice_volume:.2f}",
            "inactivity_timeout": f"{self.inactivity_timeout:.1f}",
            "wake_word_threshold": f"{self.wake_word_threshold:.2f}",
            "accent_intensity": str(self.accent_intensity),
        })

    def status_summary(self) -> Dict[str, str]:
        """
        Return safe status dictionary indicating whether services are configured.
        Never reveals secret API keys.
        """
        return {
            "NewsAPI": "Configured" if bool(self.news_api_key) else "Not Configured",
            "Groq API": "Configured" if bool(self.groq_api_key) else "Not Configured",
            "Gemini API": "Configured" if bool(self.gemini_api_key) else "Not Configured",
            "AI Provider": self.ai_provider,
            "User Name": self.user_name,
            "Voice Rate": f"{self.voice_rate} wpm",
            "Voice Volume": f"{int(self.voice_volume * 100)}%",
            "Inactivity Timeout": f"{self.inactivity_timeout}s",
        }

    def __repr__(self) -> str:
        """Safe string representation without leaking secrets."""
        summary = self.status_summary()
        return (
            f"Config(User={summary['User Name']!r}, "
            f"Provider={summary['AI Provider']!r}, "
            f"NewsAPI={summary['NewsAPI']}, "
            f"Groq={summary['Groq API']}, "
            f"Gemini={summary['Gemini API']})"
        )


_config_instance: Optional[Config] = None


def get_config(reload: bool = False) -> Config:
    """Get or create singleton Config instance."""
    global _config_instance
    if _config_instance is None or reload:
        _config_instance = Config.load()
    return _config_instance
