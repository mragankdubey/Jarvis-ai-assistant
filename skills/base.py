"""
Base Skill Interface for J.A.R.V.I.S.

Defines the standard contract for all modular skills.
Every skill must declare how it identifies matching commands and how it executes them.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class SkillResult:
    """
    Standard result returned by any skill execution.
    
    Attributes:
        success: Whether the skill executed without errors.
        message: Human-friendly text message suitable for TTS speech and display.
        data: Optional structured data payload (e.g. list of news articles, search results).
    """
    success: bool
    message: str
    data: Optional[Any] = None


class BaseSkill(ABC):
    """Abstract base class for all J.A.R.V.I.S. skills."""

    @property
    @abstractmethod
    def name(self) -> str:
        """User-friendly name of the skill."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Brief summary of what this skill does."""
        pass

    @abstractmethod
    def can_handle(self, command: str) -> bool:
        """
        Evaluate whether this skill can handle the given voice or text command.
        
        Args:
            command: Cleaned user input command string (typically lowercase).
            
        Returns:
            True if this skill is capable of handling the command.
        """
        pass

    @abstractmethod
    def execute(self, command: str, **kwargs) -> SkillResult:
        """
        Execute the skill action based on the command.
        
        Args:
            command: The user command.
            **kwargs: Additional contextual arguments if needed.
            
        Returns:
            A SkillResult describing the execution outcome.
        """
        pass
