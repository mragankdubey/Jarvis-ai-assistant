"""
AI Intelligence Engine for J.A.R.V.I.S.

Provides conversational intelligence using Groq and Google Gemini.
Includes persona prompt engineering, sliding-window conversation memory,
and graceful failover mechanisms.
"""

from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, List, Optional
import requests
from core.config import Config, get_config
from core.memory import ConversationMemory

logger = logging.getLogger(__name__)


def build_system_prompt(user_name: str = "Mragank") -> str:
    """Construct the foundational JARVIS persona system prompt."""
    return (
        f"You are J.A.R.V.I.S. (Just A Rather Very Intelligent System), the personal AI desktop assistant "
        f"inspired by the Stark Industries AI from Iron Man. You serve your creator and user, {user_name}.\n"
        f"Key behavioral guidelines:\n"
        f"1. Professional, intelligent, highly capable, concise, and subtly witty.\n"
        f"2. Keep responses brief and conversational (typically 1 to 3 sentences) because responses will be spoken aloud.\n"
        f"3. Never repeatedly introduce yourself or repeat 'I am JARVIS' unless explicitly asked who you are.\n"
        f"4. Address the user naturally by name ({user_name}) or 'sir' when appropriate, without being overly repetitive.\n"
        f"5. Acknowledge conversational context and answer follow-up questions accurately.\n"
        f"6. For calculations, facts, coding questions, or general queries, provide direct, authoritative answers."
    )


class AIProvider(ABC):
    """Abstract Base Class for AI model providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider credentials and network prerequisites are configured."""
        pass

    @abstractmethod
    def generate(self, prompt: str, history: List[Dict[str, str]], system_prompt: str) -> str:
        """Generate an AI response given prompt and dialogue history."""
        pass


_UNSET = object()


class GroqProvider(AIProvider):
    """Groq Cloud API provider using high-speed language models."""

    ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
    DEFAULT_MODELS = [
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "qwen/qwen3.8-27b",
    ]

    def __init__(self, api_key: Any = _UNSET, timeout: float = 12.0):
        self._explicit_key = api_key
        self.timeout = timeout
        self.model = self.DEFAULT_MODELS[0]

    @property
    def name(self) -> str:
        return "Groq"

    @property
    def api_key(self) -> Optional[str]:
        if self._explicit_key is not _UNSET:
            return self._explicit_key
        return get_config().groq_api_key

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate(self, prompt: str, history: List[Dict[str, str]], system_prompt: str) -> str:
        key = self.api_key
        if not key:
            raise ValueError("Groq API key is not configured.")

        messages = [{"role": "system", "content": system_prompt}]
        for turn in history:
            messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

        # Try models in list until one succeeds
        last_error = None
        for candidate_model in self.DEFAULT_MODELS:
            payload = {
                "model": candidate_model,
                "messages": messages,
                "max_tokens": 250,
                "temperature": 0.7,
            }

            try:
                response = requests.post(
                    self.ENDPOINT,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                if response.status_code == 200:
                    self.model = candidate_model
                    data = response.json()
                    return data["choices"][0]["message"]["content"].strip()
                elif response.status_code == 404:
                    # Model not available in this region/tier, try next
                    last_error = f"Model {candidate_model} not found."
                    continue
                elif response.status_code == 401:
                    raise PermissionError("Groq authentication failed. Please verify GROQ_API_KEY.")
                elif response.status_code == 429:
                    raise RuntimeError("Groq rate limit reached. Please wait a moment.")
                else:
                    raise RuntimeError(f"Groq API error (status code {response.status_code}).")

            except requests.exceptions.Timeout:
                raise TimeoutError("Groq request timed out.")
            except requests.exceptions.RequestException as e:
                raise ConnectionError(f"Network error communicating with Groq: {e}")

        raise RuntimeError(last_error or "No compatible Groq model responded.")


class GeminiProvider(AIProvider):
    """Google Gemini API provider using the official google-genai SDK."""

    DEFAULT_MODEL = "gemini-2.5-flash"

    def __init__(self, api_key: Any = _UNSET, timeout: float = 12.0):
        self._explicit_key = api_key
        self.timeout = timeout

    @property
    def name(self) -> str:
        return "Gemini"

    @property
    def api_key(self) -> Optional[str]:
        if self._explicit_key is not _UNSET:
            return self._explicit_key
        return get_config().gemini_api_key

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate(self, prompt: str, history: List[Dict[str, str]], system_prompt: str) -> str:
        key = self.api_key
        if not key:
            raise ValueError("Gemini API key is not configured.")

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=key)

            # Build conversation history contents
            contents = []
            for turn in history:
                role = "user" if turn["role"] == "user" else "model"
                contents.append(types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=turn["content"])]
                ))
            contents.append(types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)]
            ))

            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=250,
                temperature=0.7,
            )

            response = client.models.generate_content(
                model=self.DEFAULT_MODEL,
                contents=contents,
                config=config,
            )
            if response and response.text:
                return response.text.strip()
            return "I processed your request, but received an empty response, sir."

        except Exception as e:
            err_msg = str(e)
            if "API_KEY_INVALID" in err_msg or "401" in err_msg:
                raise PermissionError("Gemini authentication failed. Please verify GEMINI_API_KEY.")
            elif "429" in err_msg:
                raise RuntimeError("Gemini rate limit exceeded.")
            raise RuntimeError(f"Gemini service error: {err_msg}")


class AIEngine:
    """
    Central AI conversational engine managing active providers and memory context.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or get_config()
        self.memory = ConversationMemory(max_turns=12)
        self.groq = GroqProvider(api_key=self.config.groq_api_key)
        self.gemini = GeminiProvider(api_key=self.config.gemini_api_key)

    @property
    def active_provider(self) -> Optional[AIProvider]:
        """Determine active provider based on configuration and availability."""
        pref = self.config.ai_provider.lower()
        if pref == "groq" and self.groq.is_available():
            return self.groq
        if pref == "gemini" and self.gemini.is_available():
            return self.gemini

        # Auto selection: prefer Groq for fastest voice turnaround, fallback to Gemini
        if self.groq.is_available():
            return self.groq
        if self.gemini.is_available():
            return self.gemini
        return None

    def ask(self, user_prompt: str) -> str:
        """
        Send user prompt to active AI provider and retain context in memory.
        
        Args:
            user_prompt: User's conversational query.
            
        Returns:
            AI response string.
        """
        cleaned = user_prompt.strip()
        if not cleaned:
            return "How may I assist you, Mragank?"

        provider = self.active_provider
        if not provider:
            return (
                "I am unable to access my neural brain at the moment, sir. "
                "Neither Groq nor Gemini API keys are configured in your .env file."
            )

        system_prompt = build_system_prompt(self.config.user_name)
        history = self.memory.get_context()

        try:
            logger.info("Generating response with %s...", provider.name)
            response = provider.generate(cleaned, history, system_prompt)

            # Store in conversational memory
            self.memory.add_user_message(cleaned)
            self.memory.add_assistant_message(response)
            return response

        except Exception as e:
            logger.error("AI Generation error via %s: %s", provider.name, e)
            # Try failover to alternate provider if in auto mode
            if self.config.ai_provider == "auto":
                alt = self.gemini if provider.name == "Groq" else self.groq
                if alt.is_available():
                    try:
                        logger.info("Attempting failover to %s...", alt.name)
                        response = alt.generate(cleaned, history, system_prompt)
                        self.memory.add_user_message(cleaned)
                        self.memory.add_assistant_message(response)
                        return response
                    except Exception as alt_err:
                        logger.error("Failover also failed: %s", alt_err)

            return f"I encountered an issue connecting to my intelligence service: {e}"

    def clear_memory(self) -> None:
        """Reset conversation context."""
        self.memory.clear()


# Singleton engine instance
_ai_engine: Optional[AIEngine] = None


def get_ai_engine() -> AIEngine:
    """Get or create singleton AIEngine instance."""
    global _ai_engine
    if _ai_engine is None:
        _ai_engine = AIEngine()
    return _ai_engine
