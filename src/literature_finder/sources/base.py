"""Common adapter and HTTP behavior.

Adapters deliberately use public endpoints only. A failure in one adapter is
returned to the caller so that another source can still complete the search.
"""

from __future__ import annotations

import logging
import os
import time
from abc import ABC, abstractmethod
from typing import Any

import requests

from ..models import LiteratureRecord

LOGGER = logging.getLogger(__name__)


class SourceAdapter(ABC):
    name: str

    @abstractmethod
    def search(self, query: str, *, limit: int = 20) -> list[LiteratureRecord]:
        """Search a single query and return source-normalized records."""


class HttpClient:
    """Small retrying client with conservative defaults and a clear User-Agent."""

    def __init__(self, *, timeout: float = 20.0, retries: int = 2, min_interval: float = 0.25) -> None:
        self.timeout = timeout
        self.retries = retries
        self.min_interval = min_interval
        self._last_request = 0.0
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "academic-literature-search/0.1 (lawful research tool)"}
        )

    def get_json(self, url: str, *, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> dict[str, Any]:
        response = self.request("GET", url, params=params, headers=headers)
        return response.json()

    def request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            elapsed = time.monotonic() - self._last_request
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
            try:
                response = self.session.request(method, url, timeout=self.timeout, **kwargs)
                self._last_request = time.monotonic()
                response.raise_for_status()
                return response
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                if attempt < self.retries:
                    time.sleep(min(8.0, 0.75 * (2**attempt)))
        raise RuntimeError(f"request failed for {url}: {last_error}") from last_error


def first_nonempty(*values: Any) -> Any:
    return next((value for value in values if value not in (None, "", [])), None)


def env(name: str) -> str | None:
    value = os.getenv(name, "").strip()
    return value or None

