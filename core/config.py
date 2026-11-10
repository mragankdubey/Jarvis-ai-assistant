"""
Configuration Management Module for J.A.R.V.I.S.

Loads settings from environment variables and .env file securely.
Never exposes secret values in logs or representations.
"""

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Dict, Optional
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
    voice_rate: int = 180
    voice_volume: float = 1.0
    
    # Speech Recognition settings
    stt_timeout: float = 5.0
    stt_phrase_time_limit: float = 8.0
    stt_ambient_duration: float = 1.0
    
    # Wake Word settings
    wake_word_model: str = "hey_jarvis"
    wake_word_threshold: float = 0.5
    inactivity_timeout: float = 10.0  # seconds of silence before returning to IDLE

    @classmethod
    def load(cls) -> "Config":
        """Load and return configuration from environment variables."""
        # Check standard and backward-compatible environment variable names
        news_key = os.getenv("NEWS_API_KEY") or os.getenv("newsapi_key") or None
        if news_key:
            news_key = news_key.strip().strip('"').strip("'")
            
        groq_key = os.getenv("GROQ_API_KEY") or None
        if groq_key:
            groq_key = groq_key.strip().strip('"').strip("'")
            
        gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or None
        if gemini_key:
            gemini_key = gemini_key.strip().strip('"').strip("'")

        # Parse voice rate
        raw_rate = os.getenv("JARVIS_VOICE_RATE", "180")
        try:
            voice_rate = int(raw_rate)
        except ValueError:
            voice_rate = 180

        # Parse voice volume
        raw_volume = os.getenv("JARVIS_VOICE_VOLUME", "1.0")
        try:
            voice_volume = float(raw_volume)
            voice_volume = max(0.0, min(1.0, voice_volume))
        except ValueError:
            voice_volume = 1.0

        user_name = os.getenv("JARVIS_USER_NAME", "Mragank").strip() or "Mragank"
        ai_provider = os.getenv("AI_PROVIDER", "auto").strip().lower()

        # Parse inactivity timeout
        try:
            inactivity = float(os.getenv("JARVIS_INACTIVITY_TIMEOUT", "10.0"))
        except ValueError:
            inactivity = 10.0

        return cls(
            user_name=user_name,
            ai_provider=ai_provider,
            news_api_key=news_key,
            groq_api_key=groq_key,
            gemini_api_key=gemini_key,
            voice_rate=voice_rate,
            voice_volume=voice_volume,
            inactivity_timeout=inactivity,
        )

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


# Cached configuration instance
_config_instance: Optional[Config] = None


def get_config(reload: bool = False) -> Config:
    """Get or create singleton Config instance."""
    global _config_instance
    if _config_instance is None or reload:
        _config_instance = Config.load()
    return _config_instance
