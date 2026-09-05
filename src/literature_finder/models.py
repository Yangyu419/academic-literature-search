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

