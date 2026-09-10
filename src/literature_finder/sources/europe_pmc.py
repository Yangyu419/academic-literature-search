"""Europe PMC REST API adapter for public article metadata and full-text links."""

from __future__ import annotations

from typing import Any

from ..metadata import normalize_doi
from ..models import LiteratureRecord
from .base import HttpClient, SourceAdapter, first_nonempty


class EuropePmcAdapter(SourceAdapter):
    name = "Europe PMC"

    def __init__(self, client: HttpClient | None = None) -> None:
        self.client = client or HttpClient(min_interval=0.5)

    def search(self, query: str, *, limit: int = 20) -> list[LiteratureRecord]:
        data = self.client.get_json(
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
            params={"query": query, "format": "json", "resultType": "core", "pageSize": min(limit, 100)},
        )
        results = (data.get("resultList") or {}).get("result", []) if isinstance(data, dict) else []
        return [_record(item) for item in results if isinstance(item, dict) and item.get("title")]


def _record(item: dict[str, Any]) -> LiteratureRecord:
    source = str(item.get("source") or "MED")
    record_id = str(first_nonempty(item.get("id"), item.get("pmcid"), item.get("pmid"), "")) or None
    doi = normalize_doi(item.get("doi"))
    landing = _landing(source, item)
    pdf, pdf_source = _full_text_pdf(item.get("fullTextUrlList"))
    authors = item.get("authorList", {}).get("author", []) if isinstance(item.get("authorList"), dict) else []
    names = [str(first_nonempty(author.get("fullName"), author.get("lastName"), "")) for author in authors if isinstance(author, dict)]
    return LiteratureRecord(
        title=str(item.get("title", "")).strip(),
        literature_type="期刊论文",
        publication_date=first_nonempty(item.get("firstPublicationDate"), item.get("journalInfo", {}).get("printPublicationDate")),
        source="Europe PMC",
        publisher=str((item.get("journalInfo") or {}).get("journal", {}).get("title") or "") or None,
        journal_or_source=str((item.get("journalInfo") or {}).get("journal", {}).get("title") or "") or None,
        doi=doi,
        doi_url=f"https://doi.org/{doi}" if doi else None,
        publisher_url=landing,
        landing_page_url=landing,
        open_access_url=landing if pdf else None,
        pdf_url=pdf,
        pdf_source=pdf_source,
        authors=[name for name in names if name],
        abstract=((item.get("abstractText") or "").strip() or None),
        language=item.get("language"),
        metadata_sources=["Europe PMC"],
        source_database="Europe PMC",
        source_record_id=record_id,
        source_ids={"europe_pmc": record_id} if record_id else {},
        is_open_access=bool(pdf),
        oa_status="open" if pdf else "unknown",
        raw=item,
    )


def _landing(source: str, item: dict[str, Any]) -> str | None:
    if item.get("pmcid"):
        return f"https://europepmc.org/articles/{item['pmcid']}"
    if item.get("id"):
        return f"https://europepmc.org/article/{source}/{item['id']}"
    return None


def _full_text_pdf(value: Any) -> tuple[str | None, str | None]:
    links = value.get("fullTextUrl") if isinstance(value, dict) else value
    for link in links or []:
        if not isinstance(link, dict):
            continue
        url = link.get("url")
        style = str(link.get("documentStyle") or "").casefold()
        if url and (style == "pdf" or str(url).casefold().endswith(".pdf")):
            return str(url), str(link.get("site") or "Europe PMC")
    return None, None
