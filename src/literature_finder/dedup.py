"""Deterministic DOI/title deduplication."""

from __future__ import annotations

from difflib import SequenceMatcher

from .metadata import merge_record, normalize_title
from .models import LiteratureRecord


def deduplicate(records: list[LiteratureRecord]) -> list[LiteratureRecord]:
    result: list[LiteratureRecord] = []
    by_doi: dict[str, LiteratureRecord] = {}
    by_title: dict[str, LiteratureRecord] = {}
    for record in records:
        record.doi = record.doi or None
        doi_key = record.doi.casefold() if record.doi else None
        title_key = normalize_title(record.title)
        existing = by_doi.get(doi_key) if doi_key else by_title.get(title_key)
        if existing is None:
            for candidate in result:
                if title_key and normalize_title(candidate.title) == title_key:
                    existing = candidate
                    break
                if title_key and SequenceMatcher(None, title_key, normalize_title(candidate.title)).ratio() >= 0.96:
                    existing = candidate
                    break
        if existing is None:
            result.append(record)
            if doi_key:
                by_doi[doi_key] = record
            if title_key:
                by_title[title_key] = record
        else:
            merge_record(existing, record)
            if doi_key:
                by_doi[doi_key] = existing
    return result

