"""Voice services package for J.A.R.V.I.S."""

from voice.text_to_speech import TextToSpeech, get_tts, speak, stop, shutdown
from voice.speech_recognition import SpeechRecognizer, get_recognizer, calibrate, listen

__all__ = [
    "TextToSpeech",
    "get_tts",
    "speak",
    "stop",
    "shutdown",
    "SpeechRecognizer",
    "get_recognizer",
    "calibrate",
    "listen",
]
