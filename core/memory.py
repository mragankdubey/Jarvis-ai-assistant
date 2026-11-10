"""
In-Memory Conversation Context Manager for J.A.R.V.I.S.

Maintains a sliding-window conversational history in RAM for multi-turn dialogue.
"""

from dataclasses import dataclass
import time
from typing import List, Dict, Optional


@dataclass
class ChatTurn:
    """Represents a single message exchange."""
    role: str  # 'user' or 'assistant' or 'system'
    content: str
    timestamp: float = 0.0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()


class ConversationMemory:
    """
    Manages recent conversational history with a sliding-window maximum size.
    """

    def __init__(self, max_turns: int = 12):
        """
        Args:
            max_turns: Maximum number of user+assistant turns to retain.
        """
        self.max_turns = max_turns
        self._history: List[ChatTurn] = []

    def add_user_message(self, message: str) -> None:
        """Add a user utterance to memory."""
        cleaned = message.strip()
        if cleaned:
            self._history.append(ChatTurn(role="user", content=cleaned))
            self._trim()

    def add_assistant_message(self, message: str) -> None:
        """Add an assistant response to memory."""
        cleaned = message.strip()
        if cleaned:
            self._history.append(ChatTurn(role="assistant", content=cleaned))
            self._trim()

    def get_context(self) -> List[Dict[str, str]]:
        """Return history as standard list of role-content dicts."""
        return [{"role": turn.role, "content": turn.content} for turn in self._history]

    def clear(self) -> None:
        """Clear all stored dialogue history."""
        self._history.clear()

    def _trim(self) -> None:
        """Enforce maximum window size."""
        if len(self._history) > self.max_turns:
            self._history = self._history[-self.max_turns:]

    def __len__(self) -> int:
        return len(self._history)
