"""Skills package for J.A.R.V.I.S."""

from skills.base import BaseSkill, SkillResult
from skills.browser import BrowserSkill
from skills.news import NewsSkill
from skills.desktop import DesktopSkill

__all__ = [
    "BaseSkill",
    "SkillResult",
    "BrowserSkill",
    "NewsSkill",
    "DesktopSkill",
]
