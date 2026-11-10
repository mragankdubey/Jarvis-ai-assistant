"""
Asynchronous Text-to-Speech (TTS) Engine for J.A.R.V.I.S.

Uses a persistent background worker thread and pyttsx3 with SAPI5.
Keeps COM initialization and pyttsx3 calls on the same thread to prevent crashes.
Provides non-blocking speech playback, request queuing, and clean interruption.
"""

from dataclasses import dataclass
import logging
import queue
import threading
import time
from typing import Callable, Optional

# Configure module logger
logger = logging.getLogger(__name__)

# Try importing pythoncom for Windows COM initialization
try:
    import pythoncom
    HAS_PYTHONCOM = True
except ImportError:
    HAS_PYTHONCOM = False


@dataclass
class _SpeechItem:
    """Internal container for a queued speech request."""
    text: str
    done_event: Optional[threading.Event] = None


class TTSWorker(threading.Thread):
    """
    Persistent background worker thread that owns the pyttsx3 engine.
    Ensures that pyttsx3 is initialized and run on the same thread.
    """

    def __init__(self, rate: int = 180, volume: float = 1.0):
        super().__init__(name="JarvisTTSWorker", daemon=True)
        self.rate = rate
        self.volume = max(0.0, min(1.0, volume))
        self.queue: "queue.Queue[Optional[_SpeechItem]]" = queue.Queue()
        self._stop_event = threading.Event()
        self._is_speaking = False
        self._current_engine = None

    @property
    def is_speaking(self) -> bool:
        """Return True if the engine is currently speaking or has queued items."""
        return self._is_speaking or not self.queue.empty()

    def run(self) -> None:
        """Worker thread entry point."""
        com_initialized = False
        if HAS_PYTHONCOM:
            try:
                pythoncom.CoInitialize()
                com_initialized = True
            except Exception as e:
                logger.warning("Could not initialize COM in TTS worker: %s", e)

        engine = None
        try:
            import pyttsx3
            engine = pyttsx3.init()
            self._current_engine = engine

            # Configure speech rate and volume
            try:
                engine.setProperty("rate", self.rate)
                engine.setProperty("volume", self.volume)
            except Exception as e:
                logger.warning("Failed setting TTS properties: %s", e)

            while not self._stop_event.is_set():
                try:
                    # Timeout allows checking _stop_event periodically
                    item = self.queue.get(timeout=0.2)
                except queue.Empty:
                    continue

                if item is None:
                    # Sentinel value to exit worker loop
                    self.queue.task_done()
                    break

                text = item.text.strip()
                if not text:
                    self.queue.task_done()
                    if item.done_event:
                        item.done_event.set()
                    continue

                self._is_speaking = True
                try:
                    print(f"JARVIS SPEAKING: {text}")
                    engine.say(text)
                    engine.runAndWait()
                except Exception as e:
                    logger.error("Error during speech synthesis: %s", e)
                finally:
                    self._is_speaking = False
                    self.queue.task_done()
                    if item.done_event:
                        item.done_event.set()

        except Exception as e:
            logger.error("Critical failure in TTS worker thread: %s", e)
        finally:
            self._is_speaking = False
            self._current_engine = None
            if com_initialized and HAS_PYTHONCOM:
                try:
                    pythoncom.CoUninitialize()
                except Exception:
                    pass

    def stop_speaking(self) -> None:
        """Interrupt current speech and flush pending requests in queue."""
        # Drain all pending items from queue
        while not self.queue.empty():
            try:
                item = self.queue.get_nowait()
                if item and item.done_event:
                    item.done_event.set()
                self.queue.task_done()
            except (queue.Empty, ValueError):
                break

        # Stop active utterance in pyttsx3 engine
        if self._current_engine is not None:
            try:
                self._current_engine.stop()
            except Exception as e:
                logger.debug("Error while stopping TTS engine: %s", e)

    def request_shutdown(self) -> None:
        """Signal worker thread to exit."""
        self._stop_event.set()
        self.stop_speaking()
        self.queue.put(None)


class TextToSpeech:
    """
    Public interface for asynchronous text-to-speech services in J.A.R.V.I.S.
    """

    def __init__(self, rate: int = 180, volume: float = 1.0):
        self.rate = rate
        self.volume = volume
        self._worker: Optional[TTSWorker] = None
        self._lock = threading.Lock()
        self._ensure_worker_started()

    def _ensure_worker_started(self) -> None:
        """Ensure the background worker thread is alive."""
        with self._lock:
            if self._worker is None or not self._worker.is_alive():
                self._worker = TTSWorker(rate=self.rate, volume=self.volume)
                self._worker.start()

    def speak(self, text: str, block: bool = False) -> None:
        """
        Speak the provided text.
        
        Args:
            text: The sentence or message to be spoken.
            block: If True, waits until speech completes before returning.
                   If False (default), returns immediately while speech plays asynchronously.
        """
        if not text or not text.strip():
            return

        self._ensure_worker_started()
        assert self._worker is not None

        done_event = threading.Event() if block else None
        item = _SpeechItem(text=text.strip(), done_event=done_event)
        self._worker.queue.put(item)

        if block and done_event is not None:
            done_event.wait()

    def stop(self) -> None:
        """Immediately stop speaking and clear any queued messages."""
        with self._lock:
            if self._worker is not None and self._worker.is_alive():
                self._worker.stop_speaking()

    def shutdown(self, timeout: float = 2.0) -> None:
        """Gracefully terminate the background TTS worker thread."""
        with self._lock:
            if self._worker is not None and self._worker.is_alive():
                self._worker.request_shutdown()
                self._worker.join(timeout=timeout)
                self._worker = None

    @property
    def is_busy(self) -> bool:
        """Return True if speech is actively playing or queued."""
        if self._worker is not None and self._worker.is_alive():
            return self._worker.is_speaking
        return False


# Singleton engine instance
_tts_instance: Optional[TextToSpeech] = None
_tts_lock = threading.Lock()


def get_tts(rate: int = 180, volume: float = 1.0) -> TextToSpeech:
    """Get or create the singleton TextToSpeech instance."""
    global _tts_instance
    with _tts_lock:
        if _tts_instance is None:
            _tts_instance = TextToSpeech(rate=rate, volume=volume)
        return _tts_instance


def speak(text: str, block: bool = False) -> None:
    """Convenience function to speak text using the singleton TTS engine."""
    engine = get_tts()
    engine.speak(text, block=block)


def stop() -> None:
    """Convenience function to stop speech output immediately."""
    if _tts_instance is not None:
        _tts_instance.stop()


def shutdown() -> None:
    """Convenience function to shut down the TTS engine on exit."""
    global _tts_instance
    with _tts_lock:
        if _tts_instance is not None:
            _tts_instance.shutdown()
            _tts_instance = None
