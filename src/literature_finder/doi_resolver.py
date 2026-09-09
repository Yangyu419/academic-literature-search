"""Conservative Crossref DOI completion; never constructs a DOI from a title."""

from __future__ import annotations

from difflib import SequenceMatcher

from .metadata import normalize_doi, normalize_title, normalize_record
from .models import LiteratureRecord
from .sources.base import HttpClient, env


class CrossrefDoiResolver:
    def __init__(self, client: HttpClient | None = None, *, title_threshold: float = 0.97) -> None:
        self.client = client or HttpClient(min_interval=0.25)
        self.title_threshold = title_threshold

    def resolve(self, record: LiteratureRecord) -> LiteratureRecord:
        normalize_record(record)
        if record.doi:
            return record
        params = {"query.title": record.title, "rows": 3, "select": "DOI,title,author,published"}
        mailto = env("CROSSREF_MAILTO")
        if mailto:
            params["mailto"] = mailto
        try:
            items = self.client.get_json("https://api.crossref.org/works", params=params).get("message", {}).get("items", [])
        except Exception:
            return record
        title_key = normalize_title(record.title)
        for item in items:
            candidate_title = (item.get("title") or [""])[0]
            if SequenceMatcher(None, title_key, normalize_title(candidate_title)).ratio() < self.title_threshold:
                continue
            doi = normalize_doi(item.get("DOI"))
            if not doi:
                continue
            record.doi = doi
            record.doi_normalized = doi
            record.doi_url = f"https://doi.org/{doi}"
            record.metadata_sources = list(dict.fromkeys(record.metadata_sources + ["Crossref DOI resolution"]))
            record.source_ids.setdefault("crossref", doi)
            record.raw.setdefault("crossref_doi_resolution", item)
            return record
        return record

    def resolve_many(self, records: list[LiteratureRecord], *, limit: int = 20) -> list[LiteratureRecord]:
        count = 0
        for record in records:
            if record.doi or count >= limit:
                continue
            self.resolve(record)
            count += 1
        return records
