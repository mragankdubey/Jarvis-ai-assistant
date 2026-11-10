"""
Deterministic Command Router for J.A.R.V.I.S.

Inspects incoming voice or text commands and dispatches them
to the appropriate registered skill.
"""

import logging
from typing import List, Optional
from skills.base import BaseSkill, SkillResult

logger = logging.getLogger(__name__)


class CommandRouter:
    """
    Routes commands to registered domain skills.
    Maintains a deterministic pipeline of skills.
    """

    def __init__(self, skills: Optional[List[BaseSkill]] = None):
        """
        Args:
            skills: Optional initial list of skills. If omitted, default skills
                    (BrowserSkill, NewsSkill, DesktopSkill) are registered automatically.
        """
        self._skills: List[BaseSkill] = []
        if skills is not None:
            for s in skills:
                self.register_skill(s)
        else:
            self.register_default_skills()

    def register_default_skills(self) -> None:
        """Register baseline skills for Phase 2 & 3."""
        from skills.browser import BrowserSkill
        from skills.news import NewsSkill
        from skills.desktop import DesktopSkill

        self.register_skill(BrowserSkill())
        self.register_skill(NewsSkill())
        self.register_skill(DesktopSkill())

    def register_skill(self, skill: BaseSkill) -> None:
        """Register a new skill into the routing table."""
        if skill not in self._skills:
            self._skills.append(skill)
            logger.debug("Registered skill: %s", skill.name)

    @property
    def skills(self) -> List[BaseSkill]:
        """Return a copy of registered skills."""
        return list(self._skills)

    def route(self, command: str) -> SkillResult:
        """
        Evaluate and dispatch a command to the first matching skill.
        
        Args:
            command: The transcribed or entered user command.
            
        Returns:
            SkillResult indicating the outcome of the command execution.
        """
        cleaned = command.strip()
        if not cleaned:
            return SkillResult(
                success=False,
                message="I did not detect any command. Please try again."
            )

        # Check each registered skill
        for skill in self._skills:
            try:
                if skill.can_handle(cleaned):
                    logger.info("Routing command %r to skill %r", cleaned, skill.name)
                    return skill.execute(cleaned)
            except Exception as e:
                logger.error("Error executing skill %s: %s", skill.name, e)
                return SkillResult(
                    success=False,
                    message=f"An error occurred while executing {skill.name}: {e}"
                )

        # Fallback for unrecognized commands
        available_hints = (
            "Try commands like: 'open google', 'open youtube', 'open whatsapp', "
            "'open github', 'play <song/video>', or 'news'."
        )
        return SkillResult(
            success=False,
            message=f"I'm sorry, I don't know how to handle: '{cleaned}'. {available_hints}"
        )
