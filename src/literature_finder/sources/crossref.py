"""Crossref REST API adapter."""

from __future__ import annotations

from ..metadata import normalize_doi
from ..models import LiteratureRecord
from .base import HttpClient, env, first_nonempty


class CrossrefAdapter:
    name = "Crossref"

    def __init__(self, client: HttpClient | None = None) -> None:
        self.client = client or HttpClient()

    def search(self, query: str, *, limit: int = 20) -> list[LiteratureRecord]:
        params = {"query.bibliographic": query, "rows": min(limit, 100), "select": "DOI,title,author,published,issued,type,container-title,URL,abstract,link"}
        mailto = env("CROSSREF_MAILTO")
        if mailto:
            params["mailto"] = mailto
        data = self.client.get_json("https://api.crossref.org/works", params=params)
        records: list[LiteratureRecord] = []
        for item in data.get("message", {}).get("items", []):
            title = (item.get("title") or [""])[0].strip()
            if not title:
                continue
            date_parts = first_nonempty(item.get("published-print"), item.get("published-online"), item.get("published"), item.get("issued"), {}) .get("date-parts", [[]])[0]
            date = "-".join(str(part).zfill(2) if index else str(part) for index, part in enumerate(date_parts)) if date_parts else None
            doi = normalize_doi(item.get("DOI"))
            records.append(LiteratureRecord(
                title=title,
                literature_type=_crossref_type(item.get("type")),
                publication_date=date,
                source=(item.get("container-title") or [None])[0],
                doi=doi,
                doi_url=f"https://doi.org/{doi}" if doi else None,
                publisher_url=item.get("URL"),
                publisher=item.get("publisher"),
                abstract=item.get("abstract"),
                authors=[a.get("given", "") + (" " if a.get("given") and a.get("family") else "") + a.get("family", "") for a in item.get("author", []) if a.get("family") or a.get("given")],
                metadata_sources=[self.name],
                source_database=self.name,
                source_record_id=doi,
                source_ids={"crossref": doi} if doi else {},
                landing_page_url=item.get("URL"),
                raw=item,
            ))
        return records


def _crossref_type(value: str | None) -> str:
    return {"journal-article": "期刊论文", "proceedings-article": "会议论文", "posted-content": "预印本", "report": "技术报告", "dissertation": "博士论文"}.get(value or "", "其他")
