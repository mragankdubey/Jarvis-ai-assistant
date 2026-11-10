"""
News Retrieval Skill for J.A.R.V.I.S.

Fetches top headlines using NewsAPI with proper timeout handling,
missing key detection, network failure resilience, and credential protection.
"""

import logging
from typing import List, Optional
import requests
from core.config import get_config
from skills.base import BaseSkill, SkillResult

logger = logging.getLogger(__name__)


class NewsSkill(BaseSkill):
    """Fetches and summarizes top headlines via NewsAPI."""

    API_ENDPOINT = "https://newsapi.org/v2/top-headlines"

    def __init__(self, api_key: Optional[str] = None, timeout: float = 10.0):
        """
        Args:
            api_key: Optional explicit API key. If omitted, loaded from Config.
            timeout: Network request timeout in seconds.
        """
        self._explicit_key = api_key
        self.timeout = timeout

    @property
    def api_key(self) -> Optional[str]:
        """Resolve API key from explicit setting or environment configuration."""
        if self._explicit_key:
            return self._explicit_key
        return get_config().news_api_key

    @property
    def name(self) -> str:
        return "News Headlines"

    @property
    def description(self) -> str:
        return "Retrieves the latest top news headlines."

    def can_handle(self, command: str) -> bool:
        cmd = command.strip().lower()
        return "news" in cmd or "headlines" in cmd

    def execute(self, command: str, **kwargs) -> SkillResult:
        key = self.api_key
        if not key:
            return SkillResult(
                success=False,
                message="News API key is not configured. Please add NEWS_API_KEY to your .env file."
            )

        params = {
            "country": "us",
            "category": "business",
            "apiKey": key,
        }

        try:
            # Mask URL in debug logs to prevent key exposure
            logger.debug("Requesting news headlines from NewsAPI...")
            response = requests.get(self.API_ENDPOINT, params=params, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()
                articles = data.get("articles", [])
                if not articles:
                    return SkillResult(
                        success=True,
                        message="No news articles found at this time.",
                        data=[]
                    )

                # Extract up to top 5 article titles
                titles: List[str] = [
                    a.get("title") for a in articles[:5] if a.get("title")
                ]

                # Format human-friendly summary for speech and display
                formatted_headlines = " Here are the top news headlines: " + " ... ".join(titles)
                return SkillResult(
                    success=True,
                    message=formatted_headlines,
                    data=titles
                )

            elif response.status_code == 401:
                return SkillResult(
                    success=False,
                    message="NewsAPI authentication failed. Please verify your NEWS_API_KEY."
                )
            elif response.status_code == 429:
                return SkillResult(
                    success=False,
                    message="NewsAPI rate limit exceeded. Please try again later."
                )
            else:
                return SkillResult(
                    success=False,
                    message=f"News service returned status code {response.status_code}."
                )

        except requests.exceptions.Timeout:
            logger.warning("News request timed out.")
            return SkillResult(
                success=False,
                message="News request timed out. Please check your internet connection."
            )
        except requests.exceptions.RequestException as e:
            logger.warning("Network failure while fetching news: %s", e)
            return SkillResult(
                success=False,
                message="Unable to connect to news service. Please check your internet connection."
            )
        except Exception as e:
            logger.error("Unexpected error retrieving news: %s", e)
            return SkillResult(
                success=False,
                message="An unexpected error occurred while retrieving news."
            )
