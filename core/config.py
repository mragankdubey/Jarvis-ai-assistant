"""
Configuration Management Module for J.A.R.V.I.S.

Loads settings from environment variables, .env files, and persisted SQLite preferences.
In packaged mode, reads user credentials exclusively from %LOCALAPPDATA%\\JARVIS\\.env
and never exposes secret values in logs or representations.
"""

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import dotenv_values, load_dotenv

from core.logging_config import register_secrets_for_redaction
from core.paths import (
    ensure_user_env_template,
    get_user_data_dir,
    get_user_env_path,
    is_frozen,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_env_files() -> None:
    """
    Load environment files safely based on runtime mode:
    - Development mode: loads repo .env first (if present), then %LOCALAPPDATA%\\JARVIS\\.env (non-overriding).
    - Frozen packaged mode: creates .env.example template if missing and loads %LOCALAPPDATA%\\JARVIS\\.env.
    """
    ensure_user_env_template()
    user_env = get_user_env_path()

    if not is_frozen():
        dev_env = PROJECT_ROOT / ".env"
        if dev_env.exists():
            load_dotenv(dotenv_path=dev_env, override=False)
        if user_env.exists():
            load_dotenv(dotenv_path=user_env, override=False)
    else:
        if user_env.exists():
            load_dotenv(dotenv_path=user_env, override=True)


_load_env_files()


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
        _load_env_files()

        news_key = os.getenv("NEWS_API_KEY") or os.getenv("newsapi_key") or None
        if news_key:
            news_key = news_key.strip().strip('"').strip("'")

        groq_key = os.getenv("GROQ_API_KEY") or None
        if groq_key:
            groq_key = groq_key.strip().strip('"').strip("'")

        gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or None
        if gemini_key:
            gemini_key = gemini_key.strip().strip('"').strip("'")

        register_secrets_for_redaction(news_key, groq_key, gemini_key)

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

    def save_api_keys_to_user_env(
        self,
        groq_key: Optional[str] = None,
        gemini_key: Optional[str] = None,
        news_key: Optional[str] = None,
    ) -> Path:
        """
        Safely persist updated API credentials into %LOCALAPPDATA%\\JARVIS\\.env
        without touching packaged binaries or source files.
        """
        env_path = get_user_env_path()
        existing = dict(dotenv_values(env_path)) if env_path.exists() else {}

        if groq_key is not None and groq_key.strip():
            self.groq_api_key = groq_key.strip()
            existing["GROQ_API_KEY"] = self.groq_api_key
            os.environ["GROQ_API_KEY"] = self.groq_api_key

        if gemini_key is not None and gemini_key.strip():
            self.gemini_api_key = gemini_key.strip()
            existing["GEMINI_API_KEY"] = self.gemini_api_key
            os.environ["GEMINI_API_KEY"] = self.gemini_api_key

        if news_key is not None and news_key.strip():
            self.news_api_key = news_key.strip()
            existing["NEWS_API_KEY"] = self.news_api_key
            os.environ["NEWS_API_KEY"] = self.news_api_key

        lines = [f'{k}="{v}"' for k, v in existing.items() if v is not None]
        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        register_secrets_for_redaction(self.news_api_key, self.groq_api_key, self.gemini_api_key)
        return env_path

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
            "User Data Dir": str(get_user_data_dir()),
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
