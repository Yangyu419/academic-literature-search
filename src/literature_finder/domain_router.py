"""Select optional specialist providers from the research topic."""

from __future__ import annotations

import re

from .sources import CoreAdapter, HalAdapter, InisAdapter, NrcAdamsAdapter, OstiAdapter
from .sources.base import SourceAdapter

_NUCLEAR_TERMS = re.compile(
    r"nuclear|fuel assembly|fuel rod|fuel pellet|fuel cladding|zirconium|pwr|核燃料|燃料棒|燃料组件|包壳|芯块|锆合金|堆芯",
    re.I,
)


def is_nuclear_topic(topic: str) -> bool:
    return bool(_NUCLEAR_TERMS.search(topic))


def specialist_adapters(topic: str) -> list[SourceAdapter]:
    """Return adapters justified by the topic; link-only providers never scrape."""
    if not is_nuclear_topic(topic):
        return [HalAdapter(), CoreAdapter()]
    return [OstiAdapter(), NrcAdamsAdapter(), InisAdapter(), HalAdapter(), CoreAdapter()]
