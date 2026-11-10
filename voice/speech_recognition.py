"""
Speech Recognition (STT) Module for J.A.R.V.I.S.

Encapsulates microphone access, ambient noise calibration, and one-shot
speech transcription using the SpeechRecognition package.
Handles network errors, timeouts, and microphone unavailability gracefully.
"""

import logging
from typing import Optional
import speech_recognition as sr

logger = logging.getLogger(__name__)


class SpeechRecognizer:
    """
    Manages microphone input and one-shot speech-to-text recognition.
    """

    def __init__(self, recognizer: Optional[sr.Recognizer] = None):
        self.recognizer = recognizer or sr.Recognizer()
        self._is_calibrated = False

    def calibrate(self, duration: float = 1.0) -> bool:
        """
        Calibrate the recognizer energy threshold for ambient noise.
        
        Args:
            duration: Duration in seconds to sample ambient background noise.
            
        Returns:
            True if calibration succeeded, False if microphone is unavailable.
        """
        try:
            print("Calibrating microphone for ambient noise...")
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=duration)
            self._is_calibrated = True
            print("Microphone calibration complete.")
            return True
        except (OSError, AttributeError) as e:
            logger.warning("Microphone unavailable for calibration: %s", e)
            print("Warning: No working microphone detected. Voice input may be unavailable.")
            return False
        except Exception as e:
            logger.error("Unexpected error during microphone calibration: %s", e)
            return False

    def listen_and_recognize(
        self,
        timeout: Optional[float] = 5.0,
        phrase_time_limit: Optional[float] = 8.0,
    ) -> Optional[str]:
        """
        Listen for a single phrase from the microphone and transcribe it.
        
        Args:
            timeout: Maximum seconds to wait for a phrase to start.
            phrase_time_limit: Maximum seconds for the phrase duration.
            
        Returns:
            Transcribed text string if successful, or None if timed out,
            unintelligible, or upon error.
        """
        try:
            with sr.Microphone() as source:
                print("Listening...")
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
                print("Recognizing...")

            text = self.recognizer.recognize_google(audio)
            cleaned = text.strip()
            print(f"Heard: {cleaned!r}")
            return cleaned

        except sr.WaitTimeoutError:
            # Normal occurrence: user remained silent
            logger.debug("Listening timed out with no speech detected.")
            return None

        except sr.UnknownValueError:
            # Normal occurrence: audio could not be matched to words
            logger.debug("Speech was unintelligible.")
            return None

        except sr.RequestError as e:
            logger.warning("Speech recognition service request error: %s", e)
            print(f"Network error with speech recognition service: {e}")
            return None

        except (OSError, AttributeError) as e:
            logger.warning("Microphone error during listening: %s", e)
            print(f"Microphone error: {e}")
            return None

        except Exception as e:
            logger.error("Unexpected error during speech recognition: %s", e)
            return None


# Singleton instance
_recognizer_instance: Optional[SpeechRecognizer] = None


def get_recognizer() -> SpeechRecognizer:
    """Get or create singleton SpeechRecognizer instance."""
    global _recognizer_instance
    if _recognizer_instance is None:
        _recognizer_instance = SpeechRecognizer()
    return _recognizer_instance


def calibrate(duration: float = 1.0) -> bool:
    """Convenience function to calibrate ambient noise using singleton recognizer."""
    return get_recognizer().calibrate(duration=duration)


def listen(
    timeout: Optional[float] = 5.0,
    phrase_time_limit: Optional[float] = 8.0,
) -> Optional[str]:
    """Convenience function for one-shot speech recognition."""
    return get_recognizer().listen_and_recognize(
        timeout=timeout,
        phrase_time_limit=phrase_time_limit,
    )
