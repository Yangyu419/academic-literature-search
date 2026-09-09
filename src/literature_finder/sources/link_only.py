"""Lawful browser hand-offs for providers without a configured API."""

from __future__ import annotations

from .base import LinkOnlyAdapter


class NrcAdamsAdapter(LinkOnlyAdapter):
    name = "NRC ADAMS"

    def __init__(self) -> None:
        super().__init__(topic_url="https://adams-search.nrc.gov/")


class InisAdapter(LinkOnlyAdapter):
    name = "IAEA INIS"

    def __init__(self) -> None:
        super().__init__(topic_url="https://inis.iaea.org/search/")
