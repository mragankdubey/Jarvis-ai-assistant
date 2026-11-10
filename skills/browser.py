"""
Browser and Web Navigation Skill for J.A.R.V.I.S.

Migrates existing browser shortcuts (Google, YouTube, WhatsApp, GitHub)
and YouTube media searches into a modular skill.
"""

import re
import urllib.parse
import webbrowser
from typing import Callable, Optional
from skills.base import BaseSkill, SkillResult


class BrowserSkill(BaseSkill):
    """Handles browser navigation and web searches."""

    # Pre-defined URL shortcuts matching original main.py functionality
    URL_TARGETS = {
        "google": ("Google", "https://www.google.com"),
        "youtube": ("YouTube", "https://www.youtube.com"),
        "whatsapp": ("WhatsApp Web", "https://web.whatsapp.com/"),
        "github": ("GitHub", "https://github.com/"),
    }

    def __init__(self, opener: Optional[Callable[[str], bool]] = None):
        """
        Args:
            opener: Optional callable to open URLs. Defaults to webbrowser.open.
                   Injectable for headless testing.
        """
        self._opener = opener or webbrowser.open

    @property
    def name(self) -> str:
        return "Browser Navigation"

    @property
    def description(self) -> str:
        return "Opens websites (Google, YouTube, WhatsApp, GitHub) and searches YouTube."

    def can_handle(self, command: str) -> bool:
        cmd = command.strip().lower()
        if not cmd:
            return False

        # Match exact "open <target>" patterns
        for key in self.URL_TARGETS:
            if f"open {key}" in cmd:
                return True

        # Match "play <song/video>" or YouTube search queries
        if cmd.startswith("play ") or "search youtube for " in cmd or "youtube search " in cmd:
            return True

        return False

    def execute(self, command: str, **kwargs) -> SkillResult:
        cmd = command.strip()
        cmd_lower = cmd.lower()

        # 1. Check for predefined website openers
        for key, (label, url) in self.URL_TARGETS.items():
            if f"open {key}" in cmd_lower:
                try:
                    self._opener(url)
                    return SkillResult(
                        success=True,
                        message=f"Opening {label}.",
                        data={"url": url, "target": label}
                    )
                except Exception as e:
                    return SkillResult(
                        success=False,
                        message=f"Failed to open {label}: {e}"
                    )

        # 2. Check for "play <query>" or YouTube search queries
        query = ""
        if cmd_lower.startswith("play "):
            query = cmd[5:].strip()
        elif "search youtube for " in cmd_lower:
            parts = re.split(r"search youtube for ", cmd, flags=re.IGNORECASE)
            if len(parts) > 1:
                query = parts[1].strip()
        elif "youtube search " in cmd_lower:
            parts = re.split(r"youtube search ", cmd, flags=re.IGNORECASE)
            if len(parts) > 1:
                query = parts[1].strip()

        if query:
            encoded_query = urllib.parse.quote_plus(query)
            search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
            try:
                self._opener(search_url)
                return SkillResult(
                    success=True,
                    message=f"Searching YouTube for {query}.",
                    data={"url": search_url, "query": query}
                )
            except Exception as e:
                return SkillResult(
                    success=False,
                    message=f"Failed to search YouTube: {e}"
                )

        return SkillResult(
            success=False,
            message="Could not determine the browser action requested."
        )
