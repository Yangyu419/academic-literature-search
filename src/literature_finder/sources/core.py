"""CORE API adapter, enabled only when CORE_API_KEY is configured."""

from __future__ import annotations

from typing import Any

from ..metadata import normalize_doi
from ..models import LiteratureRecord
from .base import HttpClient, env, first_nonempty


class CoreAdapter:
    name = "CORE"

    def __init__(self, client: HttpClient | None = None) -> None:
        self.client = client or HttpClient(min_interval=2.0)
        self.api_key = env("CORE_API_KEY")

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    @property
    def skip_reason(self) -> str | None:
        return None if self.available else "CORE_API_KEY is not configured"

    def search(self, query: str, *, limit: int = 20) -> list[LiteratureRecord]:
        if not self.api_key:
            return []
        data = self.client.get_json(
            "https://api.core.ac.uk/v3/search/works",
            params={"q": query, "limit": min(limit, 100)},
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        items = data.get("results", data.get("data", []))
        return [_record(item) for item in items if isinstance(item, dict) and item.get("title")]


def _record(item: dict[str, Any]) -> LiteratureRecord:
    core_id = str(first_nonempty(item.get("id"), item.get("coreId"), "")) or None
    doi = normalize_doi(item.get("doi"))
    links = item.get("links") or []
    link = links[0] if links and isinstance(links[0], str) else None
    landing = first_nonempty(item.get("downloadUrl"), item.get("sourceFulltextUrls", [None])[0] if item.get("sourceFulltextUrls") else None, link, item.get("url"))
    authors = item.get("authors") or []
    if authors and isinstance(authors[0], dict):
        authors = [str(a.get("name") or "") for a in authors]
    return LiteratureRecord(
        title=str(item.get("title", "")).strip(), literature_type=_type(item.get("documentType")),
        publication_date=item.get("publishedDate") or item.get("year"), source="CORE",
        doi=doi, doi_url=f"https://doi.org/{doi}" if doi else None, publisher_url=item.get("url"),
        landing_page_url=item.get("url") or landing, repository_url=landing, open_access_url=landing,
        pdf_url=item.get("downloadUrl"), pdf_source="CORE" if item.get("downloadUrl") else None,
        authors=[a for a in authors if a], abstract=item.get("abstract"), keywords=item.get("keywords") or [],
        metadata_sources=["CORE"], source_database="CORE", source_record_id=core_id,
        source_ids={"core": core_id} if core_id else {}, is_open_access=bool(landing),
        oa_status="open" if landing else "unknown", raw=item,
    )


def _type(value: str | None) -> str:
    text = (value or "").casefold()
    if "thesis" in text or "dissertation" in text:
        return "博士论文"
    if "journal" in text or "article" in text:
        return "期刊论文"
    if "conference" in text:
        return "会议论文"
    if "report" in text:
        return "技术报告"
    return "其他"
