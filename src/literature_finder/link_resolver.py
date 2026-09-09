"""Select stable lawful access pages and verify only explicit OA candidates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import LiteratureRecord
from .sources.base import HttpClient, env


@dataclass(slots=True)
class AccessCandidate:
    url: str
    priority: int
    label: str
    downloadable: bool = False
    source: str = ""
    file_type: str | None = None


class BestLegalAccessResolver:
    def __init__(self, client: HttpClient | None = None) -> None:
        self.client = client or HttpClient()

    def resolve(self, record: LiteratureRecord) -> LiteratureRecord:
        candidates = self._candidates(record)
        if candidates:
            chosen = sorted(candidates, key=lambda item: item.priority)[0]
            record.best_access_url = chosen.url
            record.best_legal_access_url = chosen.url
            record.notes = _append_note(record.notes, chosen.label)
            download_candidates = [candidate for candidate in candidates if candidate.downloadable]
            if download_candidates:
                download = sorted(download_candidates, key=lambda item: item.priority)[0]
                record.is_downloadable = True
                record.download_url = download.url
                record.pdf_url = record.pdf_url or download.url
                record.pdf_source = record.pdf_source or download.source
                record.download_source = download.source
                record.download_file_type = download.file_type or "pdf"
                record.download_permission_verified = True
        if not record.best_access_url:
            record.best_access_url = record.doi_url or record.publisher_url
            record.best_legal_access_url = record.best_access_url
        if not record.best_access_url:
            record.notes = _append_note(record.notes, "未找到合法开放全文入口")
        elif not record.download_permission_verified:
            record.notes = _append_note(record.notes, "Subscription may be required" if record.publisher_url else "仅有摘要")
        record.oa_status = record.oa_status or ("open" if record.is_open_access else "unknown")
        return record

    def resolve_many(self, records: list[LiteratureRecord]) -> list[LiteratureRecord]:
        return [self.resolve(record) for record in records]

    def enrich_with_unpaywall(self, record: LiteratureRecord) -> LiteratureRecord:
        email = env("UNPAYWALL_EMAIL")
        if not email or not record.doi:
            return record
        try:
            data = self.client.get_json(f"https://api.unpaywall.org/v2/{record.doi}", params={"email": email})
            record.raw["unpaywall"] = data
            location = data.get("best_oa_location") or _first_location(data.get("oa_locations"))
            if location and data.get("is_oa"):
                record.is_open_access = True
                record.oa_status = "open"
                record.oa_version = location.get("version") or record.oa_version
                url = location.get("url_for_landing_page") or location.get("url")
                pdf = location.get("url_for_pdf")
                if url:
                    record.open_access_url = url
                    record.repository_url = url if location.get("host_type") == "repository" else record.repository_url
                if pdf:
                    record.raw["unpaywall_pdf_url"] = pdf
                    record.pdf_url = pdf
                    record.pdf_source = "Unpaywall"
        except Exception:
            return record
        return record

    def _candidates(self, record: LiteratureRecord) -> list[AccessCandidate]:
        candidates: list[AccessCandidate] = []
        if record.download_permission_verified and record.download_url:
            candidates.append(AccessCandidate(record.download_url, 20, "官方可下载全文", True, record.download_source or "verified source", record.download_file_type))
        if record.open_access_url:
            candidates.append(AccessCandidate(record.open_access_url, 10, "Open Access", False, "OA landing page"))
        if record.repository_url:
            candidates.append(AccessCandidate(record.repository_url, 12, "机构仓储全文", False, "institutional repository"))
        if record.pdf_url and record.is_open_access:
            candidates.append(AccessCandidate(record.pdf_url, 15, "官方公开 PDF", True, record.pdf_source or "OA location", "pdf"))
        if record.raw.get("unpaywall_pdf_url") and record.raw.get("unpaywall", {}).get("is_oa"):
            candidates.append(AccessCandidate(record.raw["unpaywall_pdf_url"], 15, "官方可下载全文", True, "Unpaywall OA location"))
        semantic_oa = record.raw.get("openAccessPdf") or record.raw.get("open_access_pdf") or {}
        if semantic_oa.get("url"):
            candidates.append(AccessCandidate(semantic_oa["url"], 16, "公开全文", True, "Semantic Scholar OA location", "pdf"))
        if record.doi_url:
            candidates.append(AccessCandidate(record.doi_url, 30, "DOI 页面", False, "DOI"))
        if record.publisher_url:
            candidates.append(AccessCandidate(record.publisher_url, 40, "Publisher page", False, "publisher"))
        return candidates


def _first_location(locations: list[dict[str, Any]] | None) -> dict[str, Any] | None:
    return locations[0] if locations else None


def _append_note(existing: str | None, note: str) -> str:
    return "; ".join(dict.fromkeys(filter(None, [existing, note])))
