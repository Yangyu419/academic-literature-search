"""ABES theses.fr JSON API adapter."""

from __future__ import annotations

from typing import Any

from ..metadata import normalize_doi
from ..models import LiteratureRecord
from .base import HttpClient, SourceAdapter, first_nonempty


class ThesesFrAdapter(SourceAdapter):
    name = "theses.fr"

    def __init__(self, client: HttpClient | None = None, *, api_url: str = "https://api.theses.fr/") -> None:
        self.client = client or HttpClient(min_interval=1.0)
        self.api_url = api_url

    def search(self, query: str, *, limit: int = 20) -> list[LiteratureRecord]:
        data = self.client.get_json(self.api_url, params={"q": query, "wt": "json", "rows": min(limit, 100), "start": 0})
        docs = (data.get("response") or {}).get("docs", []) if isinstance(data, dict) else []
        return [_record(item) for item in docs if isinstance(item, dict) and _title(item)]


def _title(item: dict[str, Any]) -> str:
    value = first_nonempty(item.get("titre"), item.get("title_s"), item.get("title"), "")
    return value[0] if isinstance(value, list) else str(value)


def _record(item: dict[str, Any]) -> LiteratureRecord:
    title = _title(item).strip()
    record_id = str(first_nonempty(item.get("id"), item.get("nnt"), item.get("thesis_id"), "")) or None
    landing = first_nonempty(item.get("uri_s"), item.get("url"), f"https://theses.fr/{record_id}" if record_id else None)
    pdf = first_nonempty(item.get("fullTextUrl"), item.get("fulltext_url"), item.get("pdf_url"), item.get("url_pdf"))
    authors_value = first_nonempty(item.get("auteurs"), item.get("author_s"), item.get("authors"), [])
    if isinstance(authors_value, str):
        authors = [authors_value]
    else:
        authors = [str(a.get("nom") or a.get("name") or a) if isinstance(a, dict) else str(a) for a in authors_value or []]
    doi = normalize_doi(item.get("doi"))
    school = first_nonempty(item.get("etablissement"), item.get("institution"), item.get("school"))
    date = first_nonempty(item.get("dateSoutenance"), item.get("date"), item.get("year"))
    return LiteratureRecord(
        title=title, literature_type="博士论文", publication_date=date, source="theses.fr", publisher=school,
        doi=doi, doi_url=f"https://doi.org/{doi}" if doi else None, publisher_url=landing, landing_page_url=landing,
        repository_url=landing, open_access_url=landing if pdf else None, pdf_url=pdf, pdf_source="theses.fr" if pdf else None,
        authors=[a for a in authors if a], abstract=first_nonempty(item.get("resume"), item.get("abstract")),
        language=item.get("langue"), metadata_sources=["theses.fr"], source_database="theses.fr", source_record_id=record_id,
        source_ids={"theses_fr": record_id} if record_id else {}, is_open_access=bool(pdf), oa_status="open" if pdf else "unknown", raw=item,
    )
