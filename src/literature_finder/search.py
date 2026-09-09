"""Multi-source search orchestration with failure isolation."""

from __future__ import annotations

import logging

from .dedup import deduplicate
from .metadata import normalize_record
from .models import LiteratureRecord, ResearchRequest, SearchPlan, SearchResult, SourceFailure
from .ranking import rank_records
from .sources.base import SourceAdapter

LOGGER = logging.getLogger(__name__)
MIN_RELEVANCE_SCORE = 45.0


class SearchEngine:
    def __init__(self, adapters: list[SourceAdapter]) -> None:
        self.adapters = adapters

    def search(self, plan: SearchPlan, *, target_count: int = 30, request: ResearchRequest | None = None) -> SearchResult:
        raw: list[LiteratureRecord] = []
        failures: list[SourceFailure] = []
        per_query = max(5, min(25, (target_count * 2) // max(1, len(plan.queries))))
        for adapter in self.adapters:
            if not getattr(adapter, "available", True):
                reason = getattr(adapter, "skip_reason", None) or "provider unavailable"
                LOGGER.info("%s skipped: %s", adapter.name, reason)
                failures.append(SourceFailure(adapter.name, f"skipped: {reason}"))
                continue
            for query in plan.queries:
                try:
                    LOGGER.info("Searching %s: %s", adapter.name, query)
                    raw.extend(normalize_record(record) for record in adapter.search(query, limit=per_query))
                except Exception as exc:  # adapter failures must not abort the run
                    LOGGER.warning("%s failed: %s", adapter.name, exc)
                    failures.append(SourceFailure(adapter.name, str(exc)))
                    break
        unique = deduplicate(raw)
        ranked = rank_records(unique, request or _request_from_plan(plan, target_count))
        qualified = [record for record in ranked if (record.relevance_score or 0.0) >= MIN_RELEVANCE_SCORE]
        LOGGER.info("Relevance filter: %d/%d candidates retained (threshold %.1f)", len(qualified), len(ranked), MIN_RELEVANCE_SCORE)
        return SearchResult(qualified[:target_count], len(raw), failures)


def _request_from_plan(plan: SearchPlan, target_count: int) -> ResearchRequest:
    return ResearchRequest(
        topic=" ".join(plan.concepts),
        target_count=target_count,
        start_year=plan.filters.get("start_year"),
        end_year=plan.filters.get("end_year"),
        literature_types=plan.filters.get("literature_types", []),
    )
