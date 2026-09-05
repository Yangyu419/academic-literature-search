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


def normalize_title(title: str) -> str:
    value = unicodedata.normalize("NFKC", html.unescape(title or "")).casefold()
    value = value.replace("–", "-").replace("—", "-")
    return re.sub(r"[^\w\u4e00-\u9fff]+", "", value, flags=re.UNICODE)


def merge_record(preferred: LiteratureRecord, other: LiteratureRecord) -> LiteratureRecord:
    """Merge a duplicate without inventing values; preferred sources win conflicts."""
    for field in ("literature_type", "publication_date", "source", "doi", "abstract", "language", "publisher_url", "repository_url", "open_access_url"):
        if getattr(preferred, field) in (None, "") and getattr(other, field) not in (None, ""):
            setattr(preferred, field, getattr(other, field))
    preferred.doi = normalize_doi(preferred.doi)
    preferred.doi_url = f"https://doi.org/{preferred.doi}" if preferred.doi else preferred.doi_url
    preferred.authors = preferred.authors or other.authors
    preferred.metadata_sources = list(dict.fromkeys(preferred.metadata_sources + other.metadata_sources))
    preferred.raw.update({k: v for k, v in other.raw.items() if k not in preferred.raw})
    preferred.citation_count = max(filter(None, (preferred.citation_count, other.citation_count)), default=None)
    if other.download_permission_verified and not preferred.download_permission_verified:
        for field in ("is_downloadable", "download_url", "download_source", "download_file_type", "download_permission_verified"):
            setattr(preferred, field, getattr(other, field))
    return preferred

