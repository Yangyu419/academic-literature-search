"""Zenodo Records API adapter for public research outputs."""

from __future__ import annotations

from typing import Any

from ..metadata import normalize_doi
from ..models import LiteratureRecord
from .base import HttpClient, SourceAdapter, first_nonempty


class ZenodoAdapter(SourceAdapter):
    name = "Zenodo"

    def __init__(self, client: HttpClient | None = None) -> None:
        self.client = client or HttpClient(min_interval=0.5)

    def search(self, query: str, *, limit: int = 20) -> list[LiteratureRecord]:
        data = self.client.get_json("https://zenodo.org/api/records", params={"q": query, "size": min(limit, 100), "sort": "bestmatch"})
        hits = (data.get("hits") or {}).get("hits", []) if isinstance(data, dict) else []
        return [_record(item) for item in hits if isinstance(item, dict) and ((item.get("metadata") or {}).get("title"))]


def _record(item: dict[str, Any]) -> LiteratureRecord:
    metadata = item.get("metadata") or {}
    zenodo_id = str(first_nonempty(item.get("id"), "")) or None
    doi = normalize_doi(first_nonempty(metadata.get("doi"), item.get("doi")))
    landing = first_nonempty((item.get("links") or {}).get("self_html"), f"https://zenodo.org/records/{zenodo_id}" if zenodo_id else None)
    pdf = _pdf_link(item.get("files"))
    authors = [str(author.get("name")) for author in metadata.get("creators") or [] if isinstance(author, dict) and author.get("name")]
    doc_type = str(metadata.get("resource_type", {}).get("type") or "").casefold()
    literature_type = "预印本" if "publication" in doc_type or "presentation" in doc_type else "其他"
    return LiteratureRecord(
        title=str(metadata.get("title", "")).strip(), literature_type=literature_type,
        publication_date=first_nonempty(metadata.get("publication_date"), metadata.get("created")), source="Zenodo",
        journal_or_source="Zenodo", doi=doi, doi_url=f"https://doi.org/{doi}" if doi else None, publisher_url=landing,
        landing_page_url=landing, open_access_url=landing if pdf else None, pdf_url=pdf, pdf_source="Zenodo" if pdf else None,
        authors=authors, abstract=metadata.get("description"), keywords=[str(k) for k in metadata.get("keywords") or []],
        metadata_sources=["Zenodo"], source_database="Zenodo", source_record_id=zenodo_id,
        source_ids={"zenodo": zenodo_id} if zenodo_id else {}, is_open_access=bool(pdf), oa_status="open" if pdf else "unknown", raw=item,
    )


def _pdf_link(files: Any) -> str | None:
    for file in files or []:
        if not isinstance(file, dict):
            continue
        key = str(file.get("key") or "").casefold()
        link = first_nonempty(file.get("links", {}).get("self"), file.get("links", {}).get("download"), file.get("url"))
        if link and (key.endswith(".pdf") or str(file.get("type") or "").casefold() == "application/pdf"):
            return str(link)
    return None
