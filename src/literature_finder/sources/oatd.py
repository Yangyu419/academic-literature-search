"""OATD open thesis index adapter.

The endpoint is configurable because OATD's public site and API deployment
may change. If the endpoint is unavailable, the adapter returns no fabricated
records and exposes the official search URL for manual continuation.
"""

from __future__ import annotations

import urllib.parse
from typing import Any

from ..metadata import normalize_doi
from ..models import LiteratureRecord
from .base import HttpClient, SourceAdapter, first_nonempty


class OatdAdapter(SourceAdapter):
    name = "OATD"

    def __init__(self, client: HttpClient | None = None, *, api_url: str = "https://oatd.org/api") -> None:
        self.client = client or HttpClient(min_interval=1.0)
        self.api_url = api_url.rstrip("/")

    def search(self, query: str, *, limit: int = 20) -> list[LiteratureRecord]:
        try:
            data = self.client.get_json(self.api_url, params={"q": query, "limit": min(limit, 100), "format": "json"})
        except Exception:
            return []
        items = _items(data)
        return [_record(item) for item in items if isinstance(item, dict) and _title(item)]

    @staticmethod
    def search_url(query: str) -> str:
        return "https://oatd.org/?q=" + urllib.parse.quote_plus(query)


def _items(data: Any) -> list[Any]:
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        return []
    for key in ("results", "items", "documents", "records"):
        value = data.get(key)
        if isinstance(value, list):
            return value
        if isinstance(value, dict) and isinstance(value.get("items"), list):
            return value["items"]
    return []


def _title(item: dict[str, Any]) -> str:
    value = first_nonempty(item.get("title"), item.get("title_s"), item.get("title_t"), "")
    return value[0] if isinstance(value, list) else str(value)


def _record(item: dict[str, Any]) -> LiteratureRecord:
    title = _title(item).strip()
    raw_authors = first_nonempty(item.get("authors"), item.get("author"), item.get("author_s"), [])
    if isinstance(raw_authors, str):
        authors = [raw_authors]
    else:
        authors = [str(a.get("name") if isinstance(a, dict) else a) for a in raw_authors or []]
    record_id = str(first_nonempty(item.get("id"), item.get("oatd_id"), item.get("identifier"), "")) or None
    landing = first_nonempty(item.get("landing_page_url"), item.get("repository_url"), item.get("url"), item.get("link"))
    pdf = first_nonempty(item.get("pdf_url"), item.get("fulltext_url"), item.get("download_url"))
    doi = normalize_doi(item.get("doi"))
    year = first_nonempty(item.get("year"), item.get("publication_date"), item.get("date"))
    return LiteratureRecord(
        title=title, literature_type="博士论文" if str(item.get("degree") or "").casefold().find("doctor") >= 0 else "学位论文",
        publication_date=year, source="OATD", publisher=first_nonempty(item.get("institution"), item.get("university")),
        doi=doi, doi_url=f"https://doi.org/{doi}" if doi else None, publisher_url=landing, landing_page_url=landing,
        repository_url=landing, open_access_url=landing if pdf else None, pdf_url=pdf, pdf_source="OATD / originating repository" if pdf else None,
        authors=[a for a in authors if a and a != "None"], abstract=item.get("abstract"), language=item.get("language"),
        metadata_sources=["OATD"], source_database="OATD", source_record_id=record_id,
        source_ids={"oatd": record_id} if record_id else {}, is_open_access=bool(pdf), oa_status="open" if pdf else "unknown", raw=item,
    )
