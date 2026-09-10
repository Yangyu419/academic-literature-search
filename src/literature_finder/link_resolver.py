"""Select stable lawful access pages and public/free download candidates.

The resolver deliberately does not maintain a hard-coded domain allow-list. A
source-provided public PDF URL may be useful even when its OA flag is missing
or stale. The downloader still performs the final HTTP, content-type, PDF and
access-response checks before saving anything.
"""

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
        download_candidates = sorted(
            [candidate for candidate in candidates if candidate.downloadable],
            key=lambda item: item.priority,
        )
        record.raw["download_candidates"] = [
            {
                "url": item.url,
                "priority": item.priority,
                "label": item.label,
                "source": item.source,
                "file_type": item.file_type or "pdf",
            }
            for item in download_candidates
        ]
        if candidates:
            # Keep a stable landing page as the user-facing access link when
            # one exists; the separately sorted download list still prefers
            # the best direct public file candidate.
            access_candidates = [candidate for candidate in candidates if not candidate.downloadable] or candidates
            chosen = sorted(access_candidates, key=lambda item: item.priority)[0]
            record.best_access_url = chosen.url
            record.best_legal_access_url = chosen.url
            record.notes = _append_note(record.notes, chosen.label)
            if download_candidates:
                download = download_candidates[0]
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
        seen: set[str] = set()

        def add(candidate: AccessCandidate) -> None:
            if candidate.url and candidate.url not in seen:
                candidates.append(candidate)
                seen.add(candidate.url)

        for item in record.raw.get("download_candidates", []):
            if not isinstance(item, dict) or not item.get("url"):
                continue
            add(AccessCandidate(
                str(item["url"]), int(item.get("priority", 50)), str(item.get("label") or "公开全文候选"),
                True, str(item.get("source") or "source-provided candidate"), item.get("file_type") or "pdf",
            ))
        if record.download_permission_verified and record.download_url:
            add(AccessCandidate(record.download_url, _download_priority(record.download_source), "官方可下载全文", True, record.download_source or "verified source", record.download_file_type))
        if record.open_access_url:
            add(AccessCandidate(record.open_access_url, 10, "Open Access", False, "OA landing page"))
        if record.repository_url:
            add(AccessCandidate(record.repository_url, 12, "机构仓储全文", False, "institutional repository"))
        if record.pdf_url:
            # Do not suppress a usable public PDF merely because an upstream
            # provider did not set is_open_access. The download phase is the
            # final gate and rejects login/paywall/HTML/error responses.
            label = "官方公开 PDF" if record.is_open_access else "公开 PDF 候选（下载时验证）"
            source = record.pdf_source or ("OA location" if record.is_open_access else "source-provided PDF URL")
            add(AccessCandidate(record.pdf_url, _download_priority(source, record.is_open_access), label, True, source, "pdf"))
        if record.raw.get("unpaywall_pdf_url") and record.raw.get("unpaywall", {}).get("is_oa"):
            add(AccessCandidate(record.raw["unpaywall_pdf_url"], 12, "官方可下载全文", True, "Unpaywall OA location", "pdf"))
        semantic_oa = record.raw.get("openAccessPdf") or record.raw.get("open_access_pdf") or {}
        if semantic_oa.get("url"):
            add(AccessCandidate(semantic_oa["url"], 12, "公开全文", True, "Semantic Scholar OA location", "pdf"))
        if record.doi_url:
            add(AccessCandidate(record.doi_url, 30, "DOI 页面", False, "DOI"))
        if record.publisher_url:
            add(AccessCandidate(record.publisher_url, 40, "Publisher page", False, "publisher"))
        return candidates


def _first_location(locations: list[dict[str, Any]] | None) -> dict[str, Any] | None:
    return locations[0] if locations else None


def _append_note(existing: str | None, note: str) -> str:
    return "; ".join(dict.fromkeys(filter(None, [existing, note])))


def _download_priority(source: str | None, is_oa: bool = False) -> int:
    text = (source or "").casefold()
    if any(token in text for token in ("repository", "arxiv", "europe pmc", "hal", "zenodo", "pmc")):
        return 10
    if any(token in text for token in ("oatd", "theses.fr", "thesis")):
        return 20
    if any(token in text for token in ("doaj", "unpaywall", "semantic scholar")):
        return 30
    if any(token in text for token in ("osti", "oecd", "nea", "inl", "nrc", "inis")):
        return 40
    if "publisher" in text or "official" in text:
        return 50
    return 14 if is_oa else 50
