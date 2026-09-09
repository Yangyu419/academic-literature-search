"""Topic parsing, restrained term expansion, and query generation."""

from __future__ import annotations

import re

from .clarification import assess
from .models import ResearchRequest, SearchPlan

_EXPANSIONS = {
    "核燃料": ["nuclear fuel", "fuel assembly", "fuel rod", "fuel pellet", "fuel cladding"],
    "燃料组件": ["fuel assembly", "nuclear fuel assembly", "PWR fuel assembly", "fuel rod", "spacer grid"],
    "包壳": ["fuel cladding", "cladding material", "zirconium alloy cladding"],
    "芯块": ["fuel pellet", "nuclear fuel pellet"],
    "锆合金": ["zirconium alloy", "zirconium-based alloy", "Zr alloy"],
    "辐照损伤": ["irradiation damage", "radiation damage", "irradiation behavior"],
    "llm": ["large language model", "large language models", "LLM"],
    "large language model": ["LLM", "large language models", "language model agent"],
    "agent": ["AI agent", "LLM agent", "language model agent", "autonomous agent"],
    "memory": ["agent memory", "long-term memory", "working memory", "memory-augmented"],
    "检索增强生成": ["retrieval augmented generation", "RAG"],
    "学位论文": ["thesis", "dissertation"],
}


def parse_request(text: str, **overrides: object) -> ResearchRequest:
    start, end = _years(text)
    count_match = re.search(r"(?:前|top|目标|数量)\s*(\d{1,3})", text, re.I)
    target = int(count_match.group(1)) if count_match else 30
    if not count_match and "100" in text:
        target = 100
    types = _types(text.casefold())
    request = ResearchRequest(topic=text, target_count=max(1, min(target, 200)), start_year=start, end_year=end, literature_types=types)
    for key, value in overrides.items():
        if hasattr(request, key):
            setattr(request, key, value)
    return request


def build_plan(request: ResearchRequest) -> SearchPlan:
    decision = assess(request)
    concepts = _concepts(request.topic)
    expanded = _expanded_terms(concepts, request.topic)
    queries = _queries(concepts, expanded, request)
    filters: dict[str, object] = {}
    if request.start_year is not None:
        filters["start_year"] = request.start_year
    if request.end_year is not None:
        filters["end_year"] = request.end_year
    if request.literature_types:
        filters["literature_types"] = request.literature_types
    return SearchPlan(concepts, expanded, queries, filters, decision.needed, decision.score)


def _concepts(topic: str) -> list[str]:
    parts = [p.strip(" ,;，；。:") for p in re.split(r"\s+|[,，;；、]", topic) if p.strip()]
    return list(dict.fromkeys(parts[:20]))


def _expanded_terms(concepts: list[str], topic: str) -> list[str]:
    found: list[str] = []
    folded = topic.casefold()
    for key, values in _EXPANSIONS.items():
        if key.casefold() in folded:
            found.extend([key, *values])
    return list(dict.fromkeys(concepts + found))[:30]


def _queries(concepts: list[str], expanded: list[str], request: ResearchRequest) -> list[str]:
    base = request.topic.strip()
    queries = [base]
    for term in expanded:
        if term.casefold() == base.casefold():
            continue
        # Avoid issuing noisy one-word English searches. Keep phrases,
        # hyphenated identifiers, and Chinese terms as useful standalone
        # queries; connect ordinary English concepts to an anchor instead.
        if " " in term or "-" in term or re.search(r"[\u4e00-\u9fff]", term):
            queries.append(f'"{term}"')
    if len(expanded) >= 2:
        queries.extend([f'"{expanded[0]}" "{term}"' for term in expanded[1:8]])
    if request.literature_types:
        queries.extend([f'{base} {term}' for term in request.literature_types[:3]])
    return list(dict.fromkeys(queries))[:26]


def _years(text: str) -> tuple[int | None, int | None]:
    matches = [int(x) for x in re.findall(r"(?<!\d)(20\d{2})(?!\d)", text)]
    range_match = re.search(r"(20\d{2})\s*[-~至到]\s*(20\d{2})", text)
    if range_match:
        return int(range_match.group(1)), int(range_match.group(2))
    if len(matches) >= 2:
        return min(matches), max(matches)
    return (matches[0], matches[0]) if matches else (None, None)


def _types(text: str) -> list[str]:
    mapping = [("博士", "博士论文"), ("phd", "博士论文"), ("dissertation", "博士论文"), ("硕士", "硕士论文"), ("master", "硕士论文"), ("thesis", "硕士论文"), ("期刊", "期刊论文"), ("journal", "期刊论文"), ("会议", "会议论文"), ("conference", "会议论文"), ("报告", "技术报告"), ("report", "技术报告"), ("预印本", "预印本"), ("preprint", "预印本")]
    return list(dict.fromkeys(value for needle, value in mapping if needle in text))
