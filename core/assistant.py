"""
Central Orchestrator and Voice State Machine for J.A.R.V.I.S.

Manages assistant lifecycle across IDLE, ACTIVATING, LISTENING,
PROCESSING, SPEAKING, SLEEPING, ERROR, and STOPPING states.
Enables continuous multi-turn conversations without wake-word repetition.
"""

import logging
import threading
import time
from typing import Callable, List, Optional

from core.ai_engine import AIEngine, get_ai_engine
from core.command_router import CommandRouter
from core.config import Config, get_config
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

    def __init__(
        self,
        config: Optional[Config] = None,
        tts: Optional[TextToSpeech] = None,
        stt: Optional[SpeechRecognizer] = None,
        router: Optional[CommandRouter] = None,
        ai: Optional[AIEngine] = None,
        on_state_change: Optional[Callable[[AssistantState], None]] = None,
        on_message: Optional[Callable[[str, str], None]] = None,  # (role, text)
    ):
        self.config = config or get_config()
        self.tts = tts or get_tts(rate=self.config.voice_rate, volume=self.config.voice_volume)
        self.stt = stt or get_recognizer()
        self.router = router or CommandRouter()
        self.ai = ai or get_ai_engine()

        self.on_state_change = on_state_change
        self.on_message = on_message

        self._state = AssistantState.IDLE
        self._lock = threading.Lock()
        self._running = False
        self._loop_thread: Optional[threading.Thread] = None
        self._wake_event = threading.Event()

        # Initialize local wake-word detector
        self.wake_detector = WakeWordDetector(
            model_name=self.config.wake_word_model,
            threshold=self.config.wake_word_threshold,
            on_detected=self._on_wake_detected
        )

    @property
    def state(self) -> AssistantState:
        return self._state

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
        """Dispatch message to UI listeners."""
        if self.on_message:
            try:
                self.on_message(role, text)
            except Exception as e:
                logger.error("Error in message callback: %s", e)

    def _on_wake_detected(self) -> None:
        """Called when wake-word detector fires."""
        if self._state == AssistantState.IDLE:
            logger.info("Wake word detected in IDLE. Triggering activation.")
            self._wake_event.set()

    def start(self, voice_enabled: bool = True) -> None:
        """Start the assistant background thread."""
        with self._lock:
            if self._running:
                return
            self._running = True

        self._set_state(AssistantState.IDLE)

        if voice_enabled:
            # Calibrate mic once at start
            self.stt.calibrate(duration=self.config.stt_ambient_duration)
            self.wake_detector.start_listening()

        self._loop_thread = threading.Thread(
            target=self._orchestration_loop,
            name="JarvisOrchestratorThread",
            daemon=True
        )
        self._loop_thread.start()
        logger.info("J.A.R.V.I.S. assistant started.")

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
        self._wake_event.set()

    def _orchestration_loop(self) -> None:
        """Main lifecycle state machine loop."""
        while self._running:
            if self._state == AssistantState.IDLE:
                # Ensure wake detector is listening while IDLE
                self.wake_detector.resume()
                # Wait for wake event or timeout check
                woken = self._wake_event.wait(timeout=0.2)
                if not woken or not self._running:
                    continue
                self._wake_event.clear()

                # Transition to ACTIVATING
                self._set_state(AssistantState.ACTIVATING)
                self.wake_detector.pause()

                greeting = f"Yes, {self.config.user_name}?"
                self._notify_message("assistant", greeting)
                self.tts.speak(greeting, block=True)

                # Enter continuous conversation loop
                self._conversation_loop()

            time.sleep(0.05)

    def _conversation_loop(self) -> None:
        """Active multi-turn conversation loop until sleep command or timeout."""
        silence_start: Optional[float] = None

        while self._running:
            self._set_state(AssistantState.LISTENING)

            # Listen for user command
            heard = self.stt.listen_and_recognize(
                timeout=self.config.stt_timeout,
                phrase_time_limit=self.config.stt_phrase_time_limit
            )

            if not heard:
                # User remained silent
                if silence_start is None:
                    silence_start = time.time()
                elif time.time() - silence_start >= self.config.inactivity_timeout:
                    logger.info("Inactivity timeout reached (%ss). Returning to IDLE.", self.config.inactivity_timeout)
                    self._enter_sleep_mode("Standing by.")
                    return
                continue

            # Reset silence timer upon hearing user speech
            silence_start = None
            self._notify_message("user", heard)

            # Check for sleep/deactivation commands
            if any(trigger in heard.lower() for trigger in self.SLEEP_TRIGGERS):
                self._enter_sleep_mode("Deactivating. Call me if you need anything, sir.")
                return

            # Process the command
            self._set_state(AssistantState.PROCESSING)
            response_text = self._process_command(heard)

            # Speak the response
            self._set_state(AssistantState.SPEAKING)
            self._notify_message("assistant", response_text)
            self.tts.speak(response_text, block=True)

            # Automatically loop back to LISTENING for next turn without repeating wake word!

    def _enter_sleep_mode(self, farewell_text: str) -> None:
        """Gracefully transition to SLEEPING and back to IDLE."""
        self._set_state(AssistantState.SLEEPING)
        self._notify_message("assistant", farewell_text)
        self.tts.speak(farewell_text, block=True)
        self._set_state(AssistantState.IDLE)

    def process_text_command(self, text: str) -> str:
        """
        Process a typed text command from the GUI chat panel.
        Thread-safe entry point for GUI text interaction.
        """
        cleaned = text.strip()
        if not cleaned:
            return ""

        self._notify_message("user", cleaned)

        # Check sleep command
        if any(trigger in cleaned.lower() for trigger in self.SLEEP_TRIGGERS):
            farewell = "Standing by."
            self._notify_message("assistant", farewell)
            self.tts.speak(farewell, block=False)
            self._set_state(AssistantState.IDLE)
            return farewell

        # Process command
        self._set_state(AssistantState.PROCESSING)
        response_text = self._process_command(cleaned)

        self._set_state(AssistantState.SPEAKING)
        self._notify_message("assistant", response_text)
        self.tts.speak(response_text, block=False)
        self._set_state(AssistantState.IDLE)

        return response_text

    def _process_command(self, command: str) -> str:
        """
        Tiered command resolution:
        1. Fixed deterministic skills (Browser, Desktop automation, News)
        2. AI Brain fallback (Groq / Gemini)
        """
        # 1. Check registered skills
        result = self.router.route(command)
        if result.success:
            return result.message

        # 2. If no deterministic skill matched, send to AI Engine
        logger.info("Command not matched by local skills. Routing to AI Brain.")
        ai_response = self.ai.ask(command)
        return ai_response
