"""First-party API adapters used by the search orchestrator."""

from .arxiv import ArxivAdapter
from .base import LinkOnlyAdapter, SourceAdapter
from .core import CoreAdapter
from .crossref import CrossrefAdapter
from .doaj import DoajAdapter
from .europe_pmc import EuropePmcAdapter
from .hal import HalAdapter
from .link_only import InisAdapter, NrcAdamsAdapter
from .nuclearfuel_inl import NuclearFuelInlAdapter
from .oatd import OatdAdapter
from .oecd_nea import OecdNeaAdapter
from .openalex import OpenAlexAdapter
from .osti import OstiAdapter
from .semantic_scholar import SemanticScholarAdapter
from .theses_fr import ThesesFrAdapter
from .zenodo import ZenodoAdapter

__all__ = [
    "ArxivAdapter", "CrossrefAdapter", "OpenAlexAdapter", "SemanticScholarAdapter",
    "OstiAdapter", "CoreAdapter", "HalAdapter", "NrcAdamsAdapter", "InisAdapter",
    "EuropePmcAdapter", "DoajAdapter", "ZenodoAdapter", "OatdAdapter", "ThesesFrAdapter",
    "OecdNeaAdapter", "NuclearFuelInlAdapter", "LinkOnlyAdapter", "SourceAdapter",
]
