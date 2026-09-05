"""Unpaywall OA lookup adapter (DOI enrichment, not a discovery scraper)."""

from __future__ import annotations

from ..link_resolver import BestLegalAccessResolver
from ..models import LiteratureRecord


class UnpaywallAdapter:
    name = "Unpaywall"

    def __init__(self, resolver: BestLegalAccessResolver | None = None) -> None:
        self.resolver = resolver or BestLegalAccessResolver()

    def enrich(self, record: LiteratureRecord) -> LiteratureRecord:
        return self.resolver.enrich_with_unpaywall(record)
