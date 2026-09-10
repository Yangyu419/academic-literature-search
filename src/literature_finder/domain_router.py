"""Select optional specialist providers from the research topic."""

from __future__ import annotations

import re

from .sources import CoreAdapter, HalAdapter, InisAdapter, NrcAdamsAdapter, NuclearFuelInlAdapter, OatdAdapter, OecdNeaAdapter, OstiAdapter, ThesesFrAdapter
from .sources.base import SourceAdapter

_NUCLEAR_TERMS = re.compile(
    r"nuclear|fuel assembly|fuel rod|fuel pellet|fuel cladding|zirconium|pwr|核燃料|燃料棒|燃料组件|包壳|芯块|锆合金|堆芯",
    re.I,
)
_THESIS_TERMS = re.compile(r"thesis|dissertation|学位论文|博士|硕士|学位|doctoral|master", re.I)


def is_nuclear_topic(topic: str) -> bool:
    return bool(_NUCLEAR_TERMS.search(topic))


def specialist_adapters(topic: str) -> list[SourceAdapter]:
    """Return adapters justified by the topic; link-only providers never scrape."""
    adapters: list[SourceAdapter] = []
    if is_nuclear_topic(topic):
        # Preserve the existing nuclear HAL/CORE coverage while adding the
        # dedicated NEA and INL official publication indexes.
        adapters.extend([OstiAdapter(), NrcAdamsAdapter(), InisAdapter(), OecdNeaAdapter(), NuclearFuelInlAdapter(), HalAdapter(), CoreAdapter()])
    if _THESIS_TERMS.search(topic):
        adapters.extend([OatdAdapter(), ThesesFrAdapter()])
        if not any(adapter.name == "CORE" for adapter in adapters):
            adapters.append(CoreAdapter())
    return adapters
