"""Small robots-aware helpers for public official HTML indexes."""

from __future__ import annotations

import logging
import urllib.robotparser
from urllib.parse import urlparse

from .base import HttpClient, SourceAdapter

LOGGER = logging.getLogger(__name__)


class RobotsAwarePageAdapter(SourceAdapter):
    """Fetch public index pages without bypassing robots or access controls."""

    def __init__(self, client: HttpClient | None = None, *, respect_robots: bool = True) -> None:
        self.client = client or HttpClient(min_interval=2.0)
        self.respect_robots = respect_robots

    def _fetch_html(self, url: str) -> str | None:
        if self.respect_robots and not self._allowed_by_robots(url):
            LOGGER.info("Skipping %s because robots.txt did not permit automated access", url)
            return None
        response = self.client.request("GET", url)
        content_type = str(response.headers.get("Content-Type") or "").casefold()
        content = response.content
        response.close()
        if "html" not in content_type and not content.lstrip().startswith((b"<", b"<!")):
            return None
        return content.decode("utf-8", errors="replace")

    def _allowed_by_robots(self, url: str) -> bool:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        try:
            response = self.client.request("GET", robots_url)
            body = response.content.decode("utf-8", errors="replace")
            response.close()
        except Exception as exc:
            LOGGER.warning("Cannot verify robots.txt for %s: %s", parsed.netloc, exc)
            return False
        parser = urllib.robotparser.RobotFileParser()
        parser.set_url(robots_url)
        parser.parse(body.splitlines())
        return parser.can_fetch("academic-literature-search/0.2", url)
