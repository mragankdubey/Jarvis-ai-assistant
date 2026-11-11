"""
Local Offline Wake-Word Detection Module for J.A.R.V.I.S.

Uses openWakeWord with pre-trained ONNX models ('hey_jarvis') to detect
the activation phrase locally on the CPU without streaming audio to the cloud.
Cleanly releases the microphone stream on pause() so STT never competes for device access.
"""

import logging
import threading
import time
from typing import Callable, Optional
import numpy as np

logger = logging.getLogger(__name__)


class WakeWordDetector:
    """
    Monitors audio stream for local wake-word activation ('Hey Jarvis').
    """

    CHANNELS = 1
    RATE = 16000
    CHUNK_SIZE = 1280  # 80ms at 16kHz

    def __init__(
        self,
        model_name: str = "hey_jarvis",
        threshold: float = 0.5,
        on_detected: Optional[Callable[[], None]] = None,
        on_audio_level: Optional[Callable[[float], None]] = None,
    ):
        self.model_name = model_name
        self.threshold = threshold
        self.on_detected = on_detected
        self.on_audio_level = on_audio_level
        self._model = None
        self._audio = None
        self._stream = None
        self._running = False
        self._paused = False
        self._has_microphone = False
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None

    @property
    def has_microphone(self) -> bool:
        return self._has_microphone

    def _init_model(self) -> bool:
        """Load the local ONNX wake-word model."""
        if self._model is not None:
            return True
        try:
            from openwakeword.model import Model
            self._model = Model(
                wakeword_models=[self.model_name],
                inference_framework="onnx"
            )
            logger.info("Loaded wake-word model: %s", self.model_name)
            return True
        except Exception as e:
            logger.warning("Failed to initialize openWakeWord model (%s): %s", self.model_name, e)
            return False

    def _open_stream(self) -> bool:
        """Open PyAudio input stream exclusively when actively monitoring."""
        try:
            import pyaudio
            if self._audio is None:
                self._audio = pyaudio.PyAudio()
            if self._stream is None:
                self._stream = self._audio.open(
                    format=pyaudio.paInt16,
                    channels=self.CHANNELS,
                    rate=self.RATE,
                    input=True,
                    frames_per_buffer=self.CHUNK_SIZE
                )
            self._has_microphone = True
            return True
        except Exception as e:
            logger.warning("Could not open microphone for wake word: %s", e)
            self._has_microphone = False
            self._close_stream()
            return False

    def _close_stream(self) -> None:
        """Release PyAudio input stream so STT can acquire the microphone safely."""
        if self._stream is not None:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

        if self._audio is not None:
            try:
                self._audio.terminate()
            except Exception:
                pass
            self._audio = None

    def start_listening(self) -> bool:
        """Start background wake-word detection thread."""
        with self._lock:
            if self._running:
                return True

            if not self._init_model():
                return False

            if not self._open_stream():
                return False

            self._running = True
            self._paused = False
            self._thread = threading.Thread(
                target=self._detection_loop,
                name="JarvisWakeWordWorker",
                daemon=True
            )
            self._thread.start()
            logger.info("Wake-word listener started.")
            return True

    def pause(self) -> None:
        """Pause detection and release the microphone handle for STT."""
        with self._lock:
            self._paused = True
            self._close_stream()

    def resume(self) -> None:
        """Resume wake-word detection by re-opening the microphone stream."""
        with self._lock:
            if not self._running:
                return
            if self._paused:
                self._open_stream()
                self._paused = False

    def stop(self) -> None:
        """Stop wake-word detection and release all audio resources."""
        with self._lock:
            self._running = False
            self._paused = True
            self._close_stream()
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=1.5)
                self._thread = None
            logger.info("Wake-word listener stopped.")

    def _detection_loop(self) -> None:
        """Continuously process audio frames from the stream."""
        while self._running:
            with self._lock:
                paused = self._paused
                stream = self._stream

            if paused or stream is None:
                time.sleep(0.05)
                continue

            try:
                raw_data = stream.read(self.CHUNK_SIZE, exception_on_overflow=False)
                audio_frame = np.frombuffer(raw_data, dtype=np.int16)

                # Compute real-time normalized RMS audio level for HUD waveform
                if self.on_audio_level is not None and len(audio_frame) > 0:
                    rms = float(np.sqrt(np.mean(audio_frame.astype(np.float32) ** 2)))
                    level = min(1.0, rms / 8000.0)
                    try:
                        self.on_audio_level(level)
                    except Exception:
                        pass

                if self._model is not None:
                    prediction = self._model.predict(audio_frame)
                    score = prediction.get(self.model_name, 0.0)

                    if score >= self.threshold:
                        logger.info("Wake word detected! Score: %.3f", score)
                        self._model.reset()
                        if self.on_detected:
                            self.on_detected()
                        time.sleep(0.5)

            except Exception as e:
                logger.debug("Wake-word frame read error: %s", e)
                time.sleep(0.1)

    def is_running(self) -> bool:
        return self._running and not self._paused
