"""Official OSTI.GOV API adapter.

OSTI documents are public DOE research records. The adapter only consumes the
documented read-only records endpoint and never guesses a file URL.
"""

from __future__ import annotations

from typing import Any

from ..metadata import normalize_doi
from ..models import LiteratureRecord
from .base import HttpClient, first_nonempty


class OstiAdapter:
    name = "OSTI"

    def __init__(self, client: HttpClient | None = None) -> None:
        self.client = client or HttpClient(min_interval=0.5)

    def search(self, query: str, *, limit: int = 20) -> list[LiteratureRecord]:
        data = self.client.get_json(
            "https://www.osti.gov/api/v1/records",
            params={"q": query, "rows": min(limit, 100), "page": 1},
        )
        items = data.get("records", []) if isinstance(data, dict) else data
        return [_record(item) for item in items if isinstance(item, dict) and item.get("title")]


def _record(item: dict[str, Any]) -> LiteratureRecord:
    osti_id = str(first_nonempty(item.get("osti_id"), item.get("id"), "")) or None
    doi = normalize_doi(item.get("doi"))
    landing = first_nonempty(item.get("url"), item.get("landing_page_url"))
    pdf = first_nonempty(item.get("pdf_url"), item.get("fulltext_url"), item.get("download_url"))
    authors = item.get("authors") or item.get("author") or []
    if isinstance(authors, str):
        authors = [authors]
    elif authors and isinstance(authors[0], dict):
        authors = [str(a.get("name") or a.get("full_name") or "") for a in authors]
    return LiteratureRecord(
        title=str(item.get("title", "")).strip(),
        literature_type=_type(item.get("document_type") or item.get("type")),
        publication_date=item.get("publication_date") or item.get("date"),
        source="OSTI.GOV",
        publisher=item.get("publisher") or item.get("research_org"),
        doi=doi,
        doi_url=f"https://doi.org/{doi}" if doi else None,
        publisher_url=landing,
        landing_page_url=landing,
        repository_url=landing,
        open_access_url=landing if pdf else None,
        pdf_url=pdf,
        pdf_source="OSTI" if pdf else None,
        authors=[a for a in authors if a],
        abstract=item.get("abstract"),
        keywords=item.get("keywords") or [],
        metadata_sources=["OSTI"],
        source_database="OSTI",
        source_record_id=osti_id,
        source_ids={"osti": osti_id} if osti_id else {},
        is_open_access=bool(pdf),
        oa_status="open" if pdf else "unknown",
        raw=item,
    )


def _type(value: str | None) -> str:
    text = (value or "").casefold()
    if "report" in text:
        return "技术报告"
    if "journal" in text or "article" in text:
        return "期刊论文"
    if "conference" in text or "proceed" in text:
        return "会议论文"
    return "其他"
