"""First-party API adapters used by the search orchestrator."""

from .arxiv import ArxivAdapter
from .base import SourceAdapter
from .crossref import CrossrefAdapter
from .openalex import OpenAlexAdapter
from .semantic_scholar import SemanticScholarAdapter

__all__ = ["ArxivAdapter", "CrossrefAdapter", "OpenAlexAdapter", "SemanticScholarAdapter", "SourceAdapter"]

