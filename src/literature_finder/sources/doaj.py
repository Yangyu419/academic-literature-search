"""DOAJ article search adapter using the public v3-compatible API."""

from __future__ import annotations

import urllib.parse
from typing import Any

from ..metadata import normalize_doi
from ..models import LiteratureRecord
from .base import HttpClient, SourceAdapter, first_nonempty


class DoajAdapter(SourceAdapter):
    name = "DOAJ"

    def __init__(self, client: HttpClient | None = None, *, base_url: str = "https://doaj.org/api/v3") -> None:
        self.client = client or HttpClient(min_interval=0.5)
        self.base_url = base_url.rstrip("/")

    def search(self, query: str, *, limit: int = 20) -> list[LiteratureRecord]:
        encoded = urllib.parse.quote(query, safe="")
        data = self.client.get_json(
            f"{self.base_url}/search/articles/{encoded}",
            params={"page": 0, "pageSize": min(limit, 100)},
        )
        results = data.get("results", []) if isinstance(data, dict) else []
        return [_record(item) for item in results if isinstance(item, dict)]


def _record(item: dict[str, Any]) -> LiteratureRecord:
    bib = item.get("bibjson") or {}
    identifiers = bib.get("identifier") or []
    doi = normalize_doi(next((entry.get("id") for entry in identifiers if isinstance(entry, dict) and str(entry.get("type", "")).casefold() == "doi"), None))
    article_id = str(first_nonempty(item.get("id"), item.get("article_id"), "")) or None
    landing = f"https://doaj.org/article/{article_id}" if article_id else first_nonempty(bib.get("url"), item.get("url"))
    pdf = _pdf_link(bib.get("link"))
    authors = []
    for author in bib.get("author") or []:
        if isinstance(author, dict):
            name = first_nonempty(author.get("name"), "")
            if name:
                authors.append(str(name))
    year = bib.get("year")
    date = bib.get("publication_date") or (str(year) if year else None)
    journal = (bib.get("journal") or {}).get("title")
    return LiteratureRecord(
        title=str(bib.get("title") or "").strip(), literature_type="期刊论文", publication_date=date,
        source=str(journal or "DOAJ"), journal_or_source=str(journal or "DOAJ"), publisher=(bib.get("journal") or {}).get("publisher"),
        doi=doi, doi_url=f"https://doi.org/{doi}" if doi else None, publisher_url=landing, landing_page_url=landing,
        open_access_url=landing, pdf_url=pdf, pdf_source="DOAJ" if pdf else None, authors=authors,
        abstract=bib.get("abstract"), language=(bib.get("language") or [None])[0] if isinstance(bib.get("language"), list) else bib.get("language"),
        keywords=[str(item.get("term")) for item in (bib.get("keywords") or []) if isinstance(item, dict) and item.get("term")],
        metadata_sources=["DOAJ"], source_database="DOAJ", source_record_id=article_id,
        source_ids={"doaj": article_id} if article_id else {}, is_open_access=True, oa_status="open", raw=item,
    )


def _pdf_link(links: Any) -> str | None:
    for link in links or []:
        if not isinstance(link, dict):
            continue
        url = link.get("url")
        kind = str(link.get("type") or "").casefold()
        if url and (kind == "pdf" or str(url).casefold().split("?", 1)[0].endswith(".pdf")):
            return str(url)
    return None
