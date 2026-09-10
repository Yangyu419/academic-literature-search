"""DOI-based OA rescue used immediately before a download attempt."""

from __future__ import annotations

import urllib.parse
from typing import Any

from .link_resolver import BestLegalAccessResolver
from .metadata import normalize_doi
from .models import LiteratureRecord
from .sources.base import HttpClient, env, first_nonempty


class OpenAccessRescue:
    """Find additional source-reported OA locations without guessing URLs."""

    def __init__(self, client: HttpClient | None = None, *, email: str | None = None) -> None:
        self.client = client or HttpClient(min_interval=0.5)
        self.email = email or env("UNPAYWALL_EMAIL")

    def rescue(self, record: LiteratureRecord) -> LiteratureRecord:
        doi = normalize_doi(record.doi)
        if not doi:
            return record
        if self.email:
            self._unpaywall(record, doi)
        self._openalex(record, doi)
        BestLegalAccessResolver().resolve(record)
        return record

    def _unpaywall(self, record: LiteratureRecord, doi: str) -> None:
        try:
            data = self.client.get_json(f"https://api.unpaywall.org/v2/{doi}", params={"email": self.email})
            record.raw["unpaywall"] = data
            if not data.get("is_oa"):
                return
            location = data.get("best_oa_location") or (data.get("oa_locations") or [None])[0]
            if not isinstance(location, dict):
                return
            pdf = location.get("url_for_pdf")
            landing = location.get("url_for_landing_page") or location.get("url")
            if pdf and location.get("is_oa", True):
                record.raw.setdefault("download_candidates", []).append({"url": pdf, "priority": 12, "label": "Unpaywall OA 全文", "source": "Unpaywall", "file_type": "pdf"})
                record.raw["unpaywall_pdf_url"] = pdf
                record.pdf_url = record.pdf_url or pdf
                record.pdf_source = record.pdf_source or "Unpaywall"
            if landing:
                record.open_access_url = record.open_access_url or landing
            record.is_open_access = record.is_open_access or bool(data.get("is_oa"))
            record.oa_status = record.oa_status or ("open" if data.get("is_oa") else None)
            record.oa_version = record.oa_version or location.get("version")
        except Exception:
            return

    def _openalex(self, record: LiteratureRecord, doi: str) -> None:
        encoded = urllib.parse.quote(f"https://doi.org/{doi}", safe="")
        try:
            data = self.client.get_json(f"https://api.openalex.org/works/{encoded}")
            record.raw["openalex_rescue"] = data
            locations = data.get("locations") or []
            for location in locations:
                if not isinstance(location, dict):
                    continue
                pdf = location.get("pdf_url")
                if pdf and (location.get("is_oa") or (data.get("open_access") or {}).get("is_oa")):
                    source = (location.get("source") or {}).get("display_name") or "OpenAlex OA location"
                    record.raw.setdefault("download_candidates", []).append({"url": pdf, "priority": 10, "label": "OpenAlex OA 全文", "source": source, "file_type": "pdf"})
                landing = first_nonempty(location.get("landing_page_url"), pdf)
                if landing and not record.open_access_url and location.get("is_oa"):
                    record.open_access_url = landing
            record.is_open_access = record.is_open_access or bool((data.get("open_access") or {}).get("is_oa"))
        except Exception:
            return
