"""Shared, JSON-friendly data models for the search pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ResearchRequest:
    topic: str
    target_count: int = 30
    start_year: int | None = None
    end_year: int | None = None
    literature_types: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    countries: list[str] = field(default_factory=list)
    exclusions: list[str] = field(default_factory=list)
    download_requested: bool = False


@dataclass(slots=True)
class SearchPlan:
    concepts: list[str]
    expanded_terms: list[str]
    queries: list[str]
    filters: dict[str, Any] = field(default_factory=dict)
    clarification_needed: bool = False
    ambiguity_score: float = 0.0


@dataclass(slots=True)
class LiteratureRecord:
    title: str
    literature_type: str | None = None
    publication_date: str | None = None
    source: str | None = None
    doi: str | None = None
    best_access_url: str | None = None
    notes: str | None = None
    authors: list[str] = field(default_factory=list)
    abstract: str | None = None
    language: str | None = None
    metadata_sources: list[str] = field(default_factory=list)
    doi_url: str | None = None
    publisher_url: str | None = None
    repository_url: str | None = None
    open_access_url: str | None = None
    relevance_score: float | None = None
    is_downloadable: bool = False
    download_url: str | None = None
    download_source: str | None = None
    download_file_type: str | None = None
    download_permission_verified: bool = False
    citation_count: int | None = None
    external_ids: dict[str, str] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict, repr=False)
    # Presentation fields used by the Excel export.  DOI/access fields above
    # remain internal so the download workflow can still resolve legal files.
    title_zh: str | None = None
    research_content: str | None = None

    # Extended metadata and download bookkeeping. These fields are appended
    # to preserve the original positional constructor used by early clients.
    id: str | None = None
    title_normalized: str | None = None
    year: int | None = None
    journal_or_source: str | None = None
    publisher: str | None = None
    doi_normalized: str | None = None
    best_legal_access_url: str | None = None
    keywords: list[str] = field(default_factory=list)
    source_database: str | None = None
    source_record_id: str | None = None
    source_ids: dict[str, str] = field(default_factory=dict)
    landing_page_url: str | None = None
    is_open_access: bool = False
    oa_status: str | None = None
    oa_version: str | None = None
    pdf_url: str | None = None
    pdf_source: str | None = None
    relevance_reason: str | None = None
    download_status: str = "pending"
    download_path: str | None = None
    download_error: str | None = None
    existing_local_copy: bool = False
    existing_local_path: str | None = None
    duplicate_reason: str | None = None
    file_hash_sha256: str | None = None
    duplicate_group: str | None = None


@dataclass(slots=True)
class SourceFailure:
    source: str
    error: str


@dataclass(slots=True)
class SearchResult:
    records: list[LiteratureRecord]
    raw_candidate_count: int
    failures: list[SourceFailure] = field(default_factory=list)


@dataclass(slots=True)
class DownloadResult:
    sequence: int
    title: str
    status: str
    filename: str = ""
    source_url: str = ""
    failure_reason: str = ""
