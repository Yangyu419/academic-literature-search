"""HAL open repository search adapter using its documented Solr API."""

from __future__ import annotations

from typing import Any

from ..metadata import normalize_doi
from ..models import LiteratureRecord
from .base import HttpClient, first_nonempty


class HalAdapter:
    name = "HAL"

    def __init__(self, client: HttpClient | None = None) -> None:
        self.client = client or HttpClient(min_interval=1.0)

    def search(self, query: str, *, limit: int = 20) -> list[LiteratureRecord]:
        data = self.client.get_json(
            "https://api.hal.science/search/",
            params={"q": query, "wt": "json", "rows": min(limit, 100)},
        )
        docs = (data.get("response") or {}).get("docs", [])
        return [_record(item) for item in docs if isinstance(item, dict) and (item.get("title_s") or item.get("title_t"))]


def _record(item: dict[str, Any]) -> LiteratureRecord:
    hal_id = str(first_nonempty(item.get("docid"), item.get("halId_s"), "")) or None
    raw_title = first_nonempty(item.get("title_s"), item.get("title_t"), item.get("title"), "")
    title = raw_title[0] if isinstance(raw_title, list) else str(raw_title)
    doi = normalize_doi(first_nonempty(item.get("doiId_s"), item.get("doi_s")))
    landing = first_nonempty(item.get("uri_s"), f"https://hal.science/{hal_id}" if hal_id else None)
    pdf = first_nonempty(item.get("fileMain_s"), item.get("uri_s") if str(item.get("uri_s", "")).lower().endswith(".pdf") else None)
    authors = item.get("authFullName_s") or item.get("author_s") or []
    if isinstance(authors, str):
        authors = [authors]
    return LiteratureRecord(
        title=title.strip(), literature_type=_type(item.get("docType_s")),
        publication_date=first_nonempty(item.get("producedDate_tdate"), item.get("submittedDate_tdate")),
        source="HAL", doi=doi, doi_url=f"https://doi.org/{doi}" if doi else None,
        publisher_url=landing, landing_page_url=landing, repository_url=landing,
        open_access_url=landing, pdf_url=pdf, pdf_source="HAL" if pdf else None,
        authors=[str(a) for a in authors if a], abstract=first_nonempty(item.get("abstract_s"), item.get("abstract")),
        metadata_sources=["HAL"], source_database="HAL", source_record_id=hal_id,
        source_ids={"hal": hal_id} if hal_id else {}, is_open_access=bool(landing),
        oa_status="open" if landing else "unknown", raw=item,
    )


def _type(value: str | None) -> str:
    text = (value or "").casefold()
    if "thesis" in text:
        return "博士论文"
    if "article" in text:
        return "期刊论文"
    if "conference" in text:
        return "会议论文"
    return "其他"
