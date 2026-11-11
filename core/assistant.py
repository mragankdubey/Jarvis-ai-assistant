"""
Central Orchestrator and Voice State Machine for J.A.R.V.I.S.

Manages assistant lifecycle across IDLE, ACTIVATING, LISTENING,
PROCESSING, SPEAKING, SLEEPING, ERROR, and STOPPING states.
Enables continuous multi-turn conversations without wake-word repetition.
Coordinates persistent memory/notes storage, real microphone state, and window controls.
"""

import logging
import threading
import time
from typing import Callable, List, Optional

from core.ai_engine import AIEngine, get_ai_engine
from core.command_router import CommandRouter
from core.config import Config, get_config
from core.diagnostics import check_microphone
from core.states import AssistantState
from voice.speech_recognition import SpeechRecognizer, get_recognizer
from voice.text_to_speech import TextToSpeech, get_tts
from voice.wake_word import WakeWordDetector

logger = logging.getLogger(__name__)


class Assistant:
    """
    Central orchestrator managing voice state transitions, wake-word activation,
    multi-turn dialogues, command routing, and desktop events.
    """

    SLEEP_TRIGGERS = [
        "go to sleep",
        "stop listening",
        "deactivate",
        "sleep",
        "dismissed",
        "goodbye",
        "bye jarvis",
    ]

    WINDOW_COMMANDS = {
        "minimize jarvis": "minimize",
        "minimize window": "minimize",
        "maximize jarvis": "maximize",
        "maximize window": "maximize",
        "hide jarvis": "hide",
        "show jarvis": "show",
        "bring jarvis": "show",
    }

    def __init__(
        self,
        config: Optional[Config] = None,
        tts: Optional[TextToSpeech] = None,
        stt: Optional[SpeechRecognizer] = None,
        router: Optional[CommandRouter] = None,
        ai: Optional[AIEngine] = None,
        repo: Optional[object] = None,
        on_state_change: Optional[Callable[[AssistantState], None]] = None,
        on_message: Optional[Callable[[str, str], None]] = None,
        on_audio_level: Optional[Callable[[float], None]] = None,
        on_window_action: Optional[Callable[[str], None]] = None,
    ):
        self.config = config or get_config()
        self.tts = tts or get_tts(rate=self.config.voice_rate, volume=self.config.voice_volume)
        self.stt = stt or get_recognizer()
        self.router = router or CommandRouter()
        self.ai = ai or get_ai_engine()
        self.repo = repo

        self.on_state_change = on_state_change
        self.on_message = on_message
        self.on_audio_level = on_audio_level
        self.on_window_action = on_window_action

        self._state = AssistantState.IDLE
        self._lock = threading.Lock()
        self._running = False
        self._loop_thread: Optional[threading.Thread] = None
        self._wake_event = threading.Event()
        self.has_microphone: bool = False
        self.microphone_name: str = "Not Probed"

        self.wake_detector = WakeWordDetector(
            model_name=self.config.wake_word_model,
            threshold=self.config.wake_word_threshold,
            on_detected=self._on_wake_detected,
            on_audio_level=self._handle_audio_level,
        )

    @property
    def state(self) -> AssistantState:
        return self._state

    def _handle_audio_level(self, level: float) -> None:
        if self.on_audio_level:
            try:
                self.on_audio_level(level)
            except Exception:
                pass

    def _set_state(self, new_state: AssistantState) -> None:
        """Update state and notify observers."""
        with self._lock:
            self._state = new_state
        logger.info("State transition: %s", new_state.value)
        if self.on_state_change:
            try:
                self.on_state_change(new_state)
            except Exception as e:
                logger.error("Error in state change callback: %s", e)

    def _notify_message(self, role: str, text: str) -> None:
        """Persist message if repo available and dispatch to UI listeners."""
        if self.repo is not None:
            try:
                self.repo.add_message(role, text)
            except Exception as e:
                logger.debug("Repo add_message error: %s", e)

        if self.on_message:
            try:
                self.on_message(role, text)
            except Exception as e:
                logger.error("Error in message callback: %s", e)

    def _speak(self, text: str, block: bool = False) -> None:
        """Speak text only if voice output is enabled in configuration."""
        if self.config.voice_enabled:
            self.tts.speak(text, block=block)

    def _on_wake_detected(self) -> None:
        """Called when wake-word detector fires."""
        if self._state == AssistantState.IDLE and self.config.wake_word_enabled:
            logger.info("Wake word detected in IDLE. Triggering activation.")
            self._wake_event.set()

    def probe_audio(self) -> bool:
        """Probe microphone hardware honestly and update cached state."""
        available, mic_name, _ = check_microphone()
        self.has_microphone = available
        self.microphone_name = mic_name
        return available

    def start(self, voice_enabled: bool = True) -> None:
        """Start the assistant background thread."""
        with self._lock:
            if self._running:
                return
            self._running = True

        self._set_state(AssistantState.IDLE)

        if voice_enabled and self.config.wake_word_enabled:
            if self.probe_audio():
                self.stt.calibrate(duration=self.config.stt_ambient_duration)
                self.wake_detector.start_listening()
            else:
                logger.info("No physical microphone found; wake-word listener remains disabled.")

        self._loop_thread = threading.Thread(
            target=self._orchestration_loop,
            name="JarvisOrchestratorThread",
            daemon=True
        )
        self._loop_thread.start()
        logger.info("J.A.R.V.I.S. assistant started.")

    def apply_settings(self) -> None:
        """Apply updated runtime configuration without restarting the application."""
        self.wake_detector.threshold = self.config.wake_word_threshold
        self.tts.rate = self.config.voice_rate
        self.tts.volume = self.config.voice_volume

        if self.config.wake_word_enabled and self._running:
            if self.probe_audio() and not self.wake_detector.is_running():
                self.wake_detector.start_listening()
        else:
            self.wake_detector.stop()

    def stop(self) -> None:
        """Cleanly terminate assistant loop and child services."""
        self._set_state(AssistantState.STOPPING)
        self._running = False
        self._wake_event.set()
        self.wake_detector.stop()
        if self._loop_thread and self._loop_thread.is_alive():
            self._loop_thread.join(timeout=2.0)
            self._loop_thread = None
        self._set_state(AssistantState.IDLE)
        logger.info("J.A.R.V.I.S. assistant stopped.")

    def trigger_activation(self) -> None:
        """Manually trigger activation (from GUI mic button or shortcut)."""
        if not self.has_microphone:
            self.probe_audio()
        if not self.has_microphone:
            self._notify_message("assistant", "No active microphone detected on this system. You may interact via text input.")
            self._set_state(AssistantState.ERROR)
            time.sleep(0.1)
            self._set_state(AssistantState.IDLE)
            return
        self._wake_event.set()

    def _orchestration_loop(self) -> None:
        """Main lifecycle state machine loop."""
        while self._running:
            if self._state == AssistantState.IDLE:
                if self.config.wake_word_enabled and self.has_microphone:
                    self.wake_detector.resume()
                woken = self._wake_event.wait(timeout=0.25)
                if not woken or not self._running:
                    continue
                self._wake_event.clear()

                # Transition to ACTIVATING and release mic from wake detector
                self._set_state(AssistantState.ACTIVATING)
                self.wake_detector.pause()

                greeting = f"Yes, {self.config.user_name}?"
                self._notify_message("assistant", greeting)
                self._speak(greeting, block=True)

                # Enter continuous conversation loop
                self._conversation_loop()

            time.sleep(0.05)

    def _conversation_loop(self) -> None:
        """Active multi-turn conversation loop until sleep command or timeout."""
        silence_start: Optional[float] = None

        while self._running:
            self._set_state(AssistantState.LISTENING)

            heard = self.stt.listen_and_recognize(
                timeout=self.config.stt_timeout,
                phrase_time_limit=self.config.stt_phrase_time_limit
            )

            if not heard:
                if silence_start is None:
                    silence_start = time.time()
                elif time.time() - silence_start >= self.config.inactivity_timeout:
                    logger.info("Inactivity timeout reached (%ss). Returning to IDLE.", self.config.inactivity_timeout)
                    self._enter_sleep_mode("Standing by.")
                    return
                continue

            silence_start = None
            self._notify_message("user", heard)

            if any(trigger in heard.lower() for trigger in self.SLEEP_TRIGGERS):
                self._enter_sleep_mode("Deactivating. Call me if you need anything, sir.")
                return

            self._set_state(AssistantState.PROCESSING)
            response_text = self._process_command(heard)

            self._set_state(AssistantState.SPEAKING)
            self._notify_message("assistant", response_text)
            self._speak(response_text, block=True)

    def _enter_sleep_mode(self, farewell_text: str) -> None:
        """Gracefully transition to SLEEPING and back to IDLE."""
        self._set_state(AssistantState.SLEEPING)
        self._notify_message("assistant", farewell_text)
        self._speak(farewell_text, block=True)
        self._set_state(AssistantState.IDLE)

    def process_text_command(self, text: str) -> str:
        """
        Process a typed text command from the GUI chat panel or terminal.
        Thread-safe entry point for UI interaction.
        """
        cleaned = text.strip()
        if not cleaned:
            return ""

        self._notify_message("user", cleaned)

        if any(trigger in cleaned.lower() for trigger in self.SLEEP_TRIGGERS):
            farewell = "Standing by."
            self._notify_message("assistant", farewell)
            self._speak(farewell, block=False)
            self._set_state(AssistantState.SLEEPING)
            time.sleep(0.15)
            self._set_state(AssistantState.IDLE)
            return farewell

        self._set_state(AssistantState.PROCESSING)
        response_text = self._process_command(cleaned)

        self._set_state(AssistantState.SPEAKING)
        self._notify_message("assistant", response_text)
        self._speak(response_text, block=False)
        self._set_state(AssistantState.IDLE)

        return response_text

    def _process_command(self, command: str) -> str:
        """
        Tiered command resolution:
        1. Window management directives
        2. Fixed deterministic skills (Browser, Desktop automation, News)
        3. Memory capture ('remember that ...')
        4. AI Brain fallback (Groq / Gemini) with remembered context facts
        """
        cmd_lower = command.strip().lower()

        # 1. Window management directives
        for phrase, action in self.WINDOW_COMMANDS.items():
            if phrase in cmd_lower:
                if self.on_window_action:
                    self.on_window_action(action)
                return f"Executing window directive: {action}."

        # 2. Memory capture ('remember that ...')
        if cmd_lower.startswith("remember that ") or cmd_lower.startswith("remember "):
            fact_text = command.split("remember", 1)[1].strip()
            if fact_text.lower().startswith("that "):
                fact_text = fact_text[5:].strip()
            if fact_text and self.repo is not None:
                self.repo.add_fact(fact_text, category="user_preference")
                return f"Noted and stored in long-term memory, {self.config.user_name}: '{fact_text}'."

        # 3. Registered deterministic skills
        result = self.router.route(command)
        if result.success:
            # Also sync saved notes into SQLite if created via DesktopSkill
            if self.repo is not None and isinstance(result.data, dict) and "content" in result.data and "path" in result.data:
                try:
                    self.repo.create_note(
                        title=f"Voice Note ({result.data['content'][:28]})",
                        content=result.data["content"],
                        file_path=result.data["path"]
                    )
                except Exception:
                    pass
            return result.message

        # 4. AI Brain fallback
        logger.info("Command not matched by local skills. Routing to AI Brain.")
        facts_list: List[str] = []
        if self.repo is not None:
            try:
                facts_list = [f.fact for f in self.repo.list_facts()]
            except Exception:
                pass
        return self.ai.ask(command, facts=facts_list or None)
