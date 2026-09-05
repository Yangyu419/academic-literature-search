"""OpenAlex Works API adapter."""

from __future__ import annotations

from ..metadata import normalize_doi
from ..models import LiteratureRecord
from .base import HttpClient, env


class OpenAlexAdapter:
    name = "OpenAlex"

    def __init__(self, client: HttpClient | None = None) -> None:
        self.client = client or HttpClient()

    def search(self, query: str, *, limit: int = 20) -> list[LiteratureRecord]:
        params = {"search": query, "per-page": min(limit, 100), "select": "id,title,authorships,publication_date,primary_location,doi,type,open_access,cited_by_count,abstract_inverted_index"}
        email = env("OPENALEX_EMAIL")
        if email:
            params["mailto"] = email
        data = self.client.get_json("https://api.openalex.org/works", params=params)
        output: list[LiteratureRecord] = []
        for item in data.get("results", []):
            title = (item.get("title") or "").strip()
            if not title:
                continue
            location = item.get("primary_location") or {}
            source = (location.get("source") or {}).get("display_name")
            landing = location.get("landing_page_url")
            pdf = (location.get("pdf_url") or (location.get("source") or {}).get("pdf_url"))
            doi = normalize_doi(item.get("doi"))
            output.append(LiteratureRecord(
                title=title, literature_type=_openalex_type(item.get("type")), publication_date=item.get("publication_date"), source=source,
                doi=doi, doi_url=f"https://doi.org/{doi}" if doi else None, publisher_url=landing,
                open_access_url=landing if (item.get("open_access") or {}).get("is_oa") else None,
                repository_url=landing if (location.get("is_oa") and not source) else None,
                authors=[(a.get("author") or {}).get("display_name", "") for a in item.get("authorships", []) if (a.get("author") or {}).get("display_name")],
                abstract=_abstract(item.get("abstract_inverted_index")), citation_count=item.get("cited_by_count"), metadata_sources=[self.name], raw=item,
            ))
            if pdf and output[-1].open_access_url is None:
                output[-1].raw["openalex_pdf_url"] = pdf
        return output


def _openalex_type(value: str | None) -> str:
    return {"article": "期刊论文", "dissertation": "博士论文", "book-chapter": "其他", "proceedings-article": "会议论文", "report": "技术报告"}.get(value or "", "其他")


def _abstract(index: dict[str, list[int]] | None) -> str | None:
    if not index:
        return None
    words = []
    for word, positions in index.items():
        for position in positions:
            words.append((position, word))
    return " ".join(word for _, word in sorted(words))

