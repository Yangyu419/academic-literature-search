"""Compatibility facade for the download-permission stage."""

from __future__ import annotations

from .link_resolver import BestLegalAccessResolver
from .models import LiteratureRecord


class DownloadPermissionVerifier:
    """Keep download fields false unless the record carries explicit OA evidence."""

    def __init__(self, resolver: BestLegalAccessResolver | None = None) -> None:
        self.resolver = resolver or BestLegalAccessResolver()

    def verify(self, record: LiteratureRecord) -> LiteratureRecord:
        return self.resolver.resolve(record)

    def verify_many(self, records: list[LiteratureRecord]) -> list[LiteratureRecord]:
        return self.resolver.resolve_many(records)

