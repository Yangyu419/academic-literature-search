"""Deterministic DOI/title deduplication."""

from __future__ import annotations

from difflib import SequenceMatcher

from .metadata import merge_record, normalize_record, normalize_title
from .models import LiteratureRecord


def deduplicate(records: list[LiteratureRecord]) -> list[LiteratureRecord]:
    result: list[LiteratureRecord] = []
    by_doi: dict[str, LiteratureRecord] = {}
    by_title: dict[str, LiteratureRecord] = {}
    for record in records:
        normalize_record(record)
        doi_key = record.doi_normalized
        title_key = record.title_normalized or normalize_title(record.title)
        existing = by_doi.get(doi_key) if doi_key else None
        if existing is None and title_key:
            title_match = by_title.get(title_key)
            if title_match is not None and _compatible(record, title_match):
                existing = title_match
        if existing is None:
            for candidate in result:
                candidate_title = candidate.title_normalized or normalize_title(candidate.title)
                if title_key and candidate_title == title_key and _compatible(record, candidate):
                    existing = candidate
                    break
                if title_key and SequenceMatcher(None, title_key, candidate_title).ratio() >= 0.96 and _compatible(record, candidate):
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


def _compatible(left: LiteratureRecord, right: LiteratureRecord) -> bool:
    left_author = _author_key(left)
    right_author = _author_key(right)
    if left_author and right_author and left_author != right_author:
        return False
    if left.year and right.year and abs(left.year - right.year) > 1:
        return False
    return True


def _author_key(record: LiteratureRecord) -> str:
    """Return a comparable first-author token, tolerating blank provider data."""
    value = next((author.strip() for author in record.authors if author and author.strip()), "")
    parts = value.casefold().replace(",", " ").split()
    return parts[-1] if parts else ""
