"""
Assistant Voice and Interaction States for J.A.R.V.I.S.
"""

from enum import Enum


class AssistantState(Enum):
    """Voice interaction and operational states."""
    IDLE = "IDLE"                  # Waiting for wake word (Hey Jarvis)
    ACTIVATING = "ACTIVATING"      # Wake phrase detected, playing chime / greeting
    LISTENING = "LISTENING"        # Microphone active, capturing user command
    PROCESSING = "PROCESSING"      # Transcribing or routing command / thinking
    SPEAKING = "SPEAKING"          # TTS output active
    SLEEPING = "SLEEPING"          # Transitioning back to IDLE
    ERROR = "ERROR"                # Error state (e.g. microphone disconnected)
    STOPPING = "STOPPING"          # Shutting down assistant services
