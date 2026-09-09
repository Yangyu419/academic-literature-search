"""High-level pipeline used by the CLI and downstream Agent integrations."""

from __future__ import annotations

import logging

from .clarification import ClarificationDecision, assess
from .domain_router import specialist_adapters
from .doi_resolver import CrossrefDoiResolver
from .link_resolver import BestLegalAccessResolver
from .models import LiteratureRecord, ResearchRequest, SearchPlan, SearchResult
from .query_planner import build_plan
from .search import SearchEngine
from .sources import ArxivAdapter, CrossrefAdapter, OpenAlexAdapter, SemanticScholarAdapter
from .sources.base import HttpClient
from .sources.unpaywall import UnpaywallAdapter

LOGGER = logging.getLogger(__name__)


def default_adapters(topic: str | None = None) -> list[object]:
    base = [CrossrefAdapter(), OpenAlexAdapter(), SemanticScholarAdapter(), ArxivAdapter()]
    return base + specialist_adapters(topic or "")


def inspect_request(request: ResearchRequest) -> tuple[ClarificationDecision, SearchPlan]:
    return assess(request), build_plan(request)


def run_search(request: ResearchRequest, *, adapters: list[object] | None = None, resolver: BestLegalAccessResolver | None = None) -> tuple[SearchPlan, SearchResult]:
    decision, plan = inspect_request(request)
    if decision.needed:
        return plan, SearchResult([], 0, [])
    engine = SearchEngine(adapters or default_adapters(request.topic))
    result = engine.search(plan, target_count=request.target_count, request=request)
    CrossrefDoiResolver(HttpClient(min_interval=0.25)).resolve_many(result.records, limit=min(20, len(result.records)))
    oa = UnpaywallAdapter(resolver or BestLegalAccessResolver(HttpClient(min_interval=0.5)))
    for record in result.records:
        oa.enrich(record)
    (resolver or BestLegalAccessResolver()).resolve_many(result.records)
    return plan, result
