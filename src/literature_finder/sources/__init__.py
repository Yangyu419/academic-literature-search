"""First-party API adapters used by the search orchestrator."""

from .arxiv import ArxivAdapter
from .base import LinkOnlyAdapter, SourceAdapter
from .core import CoreAdapter
from .crossref import CrossrefAdapter
from .hal import HalAdapter
from .link_only import InisAdapter, NrcAdamsAdapter
from .openalex import OpenAlexAdapter
from .osti import OstiAdapter
from .semantic_scholar import SemanticScholarAdapter

__all__ = [
    "ArxivAdapter", "CrossrefAdapter", "OpenAlexAdapter", "SemanticScholarAdapter",
    "OstiAdapter", "CoreAdapter", "HalAdapter", "NrcAdamsAdapter", "InisAdapter",
    "LinkOnlyAdapter", "SourceAdapter",
]
