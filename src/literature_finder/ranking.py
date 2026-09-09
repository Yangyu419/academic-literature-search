"""Explainable lexical relevance ranking with source-quality and recency signals."""

from __future__ import annotations

import re
from datetime import date

from .metadata import normalize_title
from .models import LiteratureRecord, ResearchRequest


def rank_records(records: list[LiteratureRecord], request: ResearchRequest) -> list[LiteratureRecord]:
    terms = set(re.findall(r"[a-z0-9+#-]{3,}|[\u4e00-\u9fff]{2,}", normalize_title(request.topic)))
    for record in records:
        haystack = normalize_title(f"{record.title} {record.abstract or ''}")
        matches = sum(1 for term in terms if term in haystack)
        score = 30.0 + min(55.0, matches / max(1, len(terms)) * 55.0)
        if record.doi:
            score += 4
        if record.abstract:
            score += 3
        if record.open_access_url or record.repository_url:
            score += 3
        if request.start_year or request.end_year:
            year = _year(record.publication_date)
            if year and request.start_year and request.end_year and request.start_year <= year <= request.end_year:
                score += 5
            elif year and ((request.start_year and year < request.start_year) or (request.end_year and year > request.end_year)):
                score -= 15
        record.relevance_score = round(max(0.0, min(100.0, score)), 2)
        record.relevance_reason = (
            f"主题词匹配 {matches}/{max(1, len(terms))}；"
            f"{'含摘要' if record.abstract else '无摘要'}；"
            f"{'有 DOI' if record.doi else '无 DOI'}；"
            f"{'发现合法开放入口' if (record.open_access_url or record.repository_url) else '未确认开放入口'}"
        )
    return sorted(records, key=lambda item: (item.relevance_score or 0, item.citation_count or 0), reverse=True)


def _year(value: str | None) -> int | None:
    if not value:
        return None
    match = re.search(r"20\d{2}", value)
    return int(match.group()) if match else None
