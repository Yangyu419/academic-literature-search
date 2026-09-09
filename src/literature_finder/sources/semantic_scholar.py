"""Semantic Scholar Academic Graph API adapter."""

from __future__ import annotations

from ..metadata import normalize_doi
from ..models import LiteratureRecord
from .base import HttpClient, env


class SemanticScholarAdapter:
    name = "Semantic Scholar"

    def __init__(self, client: HttpClient | None = None) -> None:
        self.client = client or HttpClient(min_interval=0.5)

    def search(self, query: str, *, limit: int = 20) -> list[LiteratureRecord]:
        headers = {}
        key = env("SEMANTIC_SCHOLAR_API_KEY")
        if key:
            headers["x-api-key"] = key
        params = {"query": query, "limit": min(limit, 100), "fields": "title,authors,abstract,year,publicationDate,venue,externalIds,openAccessPdf,url,citationCount,publicationTypes"}
        data = self.client.get_json("https://api.semanticscholar.org/graph/v1/paper/search", params=params, headers=headers or None)
        output: list[LiteratureRecord] = []
        for item in data.get("data", []):
            title = (item.get("title") or "").strip()
            if not title:
                continue
            ids = item.get("externalIds") or {}
            doi = normalize_doi(ids.get("DOI"))
            oa = item.get("openAccessPdf") or {}
            record = LiteratureRecord(
                title=title, literature_type=_s2_type(item.get("publicationTypes")), publication_date=item.get("publicationDate") or (str(item["year"]) if item.get("year") else None), source=item.get("venue") or None,
                doi=doi, doi_url=f"https://doi.org/{doi}" if doi else None, publisher_url=item.get("url"), open_access_url=oa.get("url"),
                authors=[a.get("name", "") for a in item.get("authors", []) if a.get("name")], abstract=item.get("abstract"), citation_count=item.get("citationCount"), metadata_sources=[self.name], raw=item,
                source_database=self.name, source_record_id=item.get("paperId"),
                source_ids={"semantic_scholar": item.get("paperId")} if item.get("paperId") else {},
                landing_page_url=item.get("url"), is_open_access=bool(oa.get("url")),
                pdf_url=oa.get("url"), pdf_source="Semantic Scholar OA location",
            )
            output.append(record)
        return output


def _s2_type(values: list[str] | None) -> str:
    values = values or []
    if "Review" in values:
        return "期刊论文"
    if "Conference" in values:
        return "会议论文"
    return "期刊论文" if values else "其他"
