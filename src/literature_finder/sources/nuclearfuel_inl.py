"""Idaho National Laboratory Advanced Fuels Campaign page adapter."""

from __future__ import annotations

import html
import re
import urllib.parse
from pathlib import PurePosixPath

from ..models import LiteratureRecord
from .web_pages import RobotsAwarePageAdapter


class NuclearFuelInlAdapter(RobotsAwarePageAdapter):
    name = "INL Advanced Fuels Campaign"
    landing_url = "https://nuclearfuel.inl.gov/our-work/"

    def search(self, query: str, *, limit: int = 20) -> list[LiteratureRecord]:
        try:
            page = self._fetch_html(self.landing_url)
            records = _parse_inl_links(page or "", self.landing_url, limit)
            return records or [_fallback(query, self.landing_url)]
        except Exception as exc:
            return [_fallback(query, self.landing_url, str(exc))]


def _parse_inl_links(page: str, landing: str, limit: int) -> list[LiteratureRecord]:
    records: list[LiteratureRecord] = []
    for match in re.finditer(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", page, re.I | re.S):
        href, text = match.groups()
        url = urllib.parse.urljoin(landing, html.unescape(href).strip())
        parsed = urllib.parse.urlparse(url)
        if parsed.netloc.casefold() not in {"nuclearfuel.inl.gov", "inl.gov"} or not parsed.path.casefold().endswith(".pdf"):
            continue
        title = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(text))).strip()
        title = title or PurePosixPath(parsed.path).stem.replace("-", " ")
        records.append(LiteratureRecord(
            title=title, literature_type="技术报告", source="INL Advanced Fuels Campaign",
            publisher="Idaho National Laboratory", publisher_url=landing, landing_page_url=landing,
            open_access_url=landing, pdf_url=url, pdf_source="INL Advanced Fuels Campaign",
            metadata_sources=["INL Advanced Fuels Campaign"], source_database="INL Advanced Fuels Campaign",
            source_record_id=url, source_ids={"inl": url}, is_open_access=True, oa_status="open",
            raw={"landing_page": landing},
        ))
        if len(records) >= limit:
            break
    return records


def _fallback(query: str, landing: str, error: str | None = None) -> LiteratureRecord:
    record = LiteratureRecord(
        title=query, literature_type="技术报告", source="INL Advanced Fuels Campaign",
        publisher="Idaho National Laboratory", publisher_url=landing, landing_page_url=landing,
        best_access_url=landing, metadata_sources=["INL Advanced Fuels Campaign"],
        source_database="INL Advanced Fuels Campaign", notes="INL 公开出版物页解析失败，已降级为 landing page",
        raw={"landing_page": landing},
    )
    if error:
        record.raw["parse_error"] = error
    return record
