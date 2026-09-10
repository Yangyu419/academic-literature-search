"""Metadata normalization and non-hallucinatory DOI handling."""

from __future__ import annotations

import html
import re
import unicodedata

from .models import LiteratureRecord

DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.I)


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    match = DOI_RE.search(value.strip())
    if not match:
        return None
    return match.group(0).rstrip(".,;)").lower()


def normalize_source_ids(source_ids: dict[str, str] | None) -> dict[str, str]:
    """Return stable provider identifiers without inventing missing IDs."""
    return {str(key).casefold(): str(value) for key, value in (source_ids or {}).items() if value not in (None, "")}


def normalize_title(title: str) -> str:
    value = unicodedata.normalize("NFKC", html.unescape(title or "")).casefold()
    value = value.replace("–", "-").replace("—", "-")
    return re.sub(r"[^\w\u4e00-\u9fff]+", "", value, flags=re.UNICODE)


def publication_year(value: str | int | None) -> int | None:
    if value is None:
        return None
    match = re.search(r"(?<!\d)(19|20)\d{2}(?!\d)", str(value))
    return int(match.group(0)) if match else None


def normalize_record(record: LiteratureRecord) -> LiteratureRecord:
    """Populate derived identifiers while keeping all values source-derived."""
    record.doi = normalize_doi(record.doi)
    record.doi_normalized = record.doi
    record.title_normalized = normalize_title(record.title)
    record.year = record.year or publication_year(record.publication_date)
    record.journal_or_source = record.journal_or_source or record.source
    record.landing_page_url = record.landing_page_url or record.best_access_url or record.publisher_url
    record.source_database = record.source_database or (record.metadata_sources[0] if record.metadata_sources else None)
    record.source_ids = normalize_source_ids(record.source_ids or record.external_ids)
    if record.source_record_id and record.source_database:
        record.source_ids.setdefault(record.source_database.casefold(), record.source_record_id)
    record.best_legal_access_url = record.best_legal_access_url or record.best_access_url
    record.best_access_url = record.best_access_url or record.best_legal_access_url
    record.pdf_url = record.pdf_url or record.download_url
    record.pdf_source = record.pdf_source or record.download_source
    return record


def merge_record(preferred: LiteratureRecord, other: LiteratureRecord) -> LiteratureRecord:
    """Merge a duplicate without inventing values; preferred sources win conflicts."""
    for field in ("literature_type", "publication_date", "source", "journal_or_source", "publisher", "doi", "abstract", "language", "publisher_url", "repository_url", "open_access_url", "landing_page_url", "best_access_url", "best_legal_access_url", "pdf_url", "pdf_source", "oa_status", "oa_version"):
        if getattr(preferred, field) in (None, "") and getattr(other, field) not in (None, ""):
            setattr(preferred, field, getattr(other, field))
    preferred.doi = normalize_doi(preferred.doi)
    preferred.doi_normalized = preferred.doi_normalized or preferred.doi
    preferred.title_normalized = preferred.title_normalized or normalize_title(preferred.title)
    preferred.year = preferred.year or other.year or publication_year(preferred.publication_date)
    preferred.id = preferred.id or other.id
    preferred.source_record_id = preferred.source_record_id or other.source_record_id
    preferred.source_ids.update(normalize_source_ids(other.source_ids or other.external_ids))
    preferred.keywords = list(dict.fromkeys(preferred.keywords + other.keywords))
    preferred.external_ids.update(other.external_ids)
    preferred.is_open_access = preferred.is_open_access or other.is_open_access
    preferred.oa_status = preferred.oa_status or other.oa_status
    preferred.oa_version = preferred.oa_version or other.oa_version
    preferred.relevance_reason = preferred.relevance_reason or other.relevance_reason
    preferred.doi_url = f"https://doi.org/{preferred.doi}" if preferred.doi else preferred.doi_url
    preferred.authors = preferred.authors or other.authors
    preferred.metadata_sources = list(dict.fromkeys(preferred.metadata_sources + other.metadata_sources))
    preferred.raw.update({k: v for k, v in other.raw.items() if k not in preferred.raw})
    other_candidates = other.raw.get("download_candidates")
    if isinstance(other_candidates, list):
        current_candidates = preferred.raw.setdefault("download_candidates", [])
        if isinstance(current_candidates, list):
            seen_urls = {str(item.get("url")) for item in current_candidates if isinstance(item, dict) and item.get("url")}
            current_candidates.extend(
                item for item in other_candidates
                if isinstance(item, dict) and item.get("url") and str(item.get("url")) not in seen_urls
            )
    preferred.citation_count = max(filter(None, (preferred.citation_count, other.citation_count)), default=None)
    if other.download_permission_verified and not preferred.download_permission_verified:
        for field in ("is_downloadable", "download_url", "download_source", "download_file_type", "download_permission_verified"):
            setattr(preferred, field, getattr(other, field))
    return normalize_record(preferred)
