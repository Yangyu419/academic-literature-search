"""OECD Nuclear Energy Agency official publication index adapter.

The NEA publication page is an HTML index rather than a stable public JSON
API. This adapter parses only public links from the official page and falls
back to that page when parsing fails.
"""

from __future__ import annotations

import html
import re
import urllib.parse
from pathlib import PurePosixPath

from ..models import LiteratureRecord
from .web_pages import RobotsAwarePageAdapter


class OecdNeaAdapter(RobotsAwarePageAdapter):
    name = "OECD-NEA"
    base_url = "https://oecd-nea.org/tools/publication"

    def search(self, query: str, *, limit: int = 20) -> list[LiteratureRecord]:
        landing = f"{self.base_url}?query={urllib.parse.quote_plus(query)}"
        try:
            page = self._fetch_html(landing)
            records = _parse_publication_links(page or "", landing, limit)
            return records or [_fallback(query, landing, "OECD-NEA")]
        except Exception as exc:
            return [_fallback(query, landing, "OECD-NEA", str(exc))]


def _parse_publication_links(page: str, landing: str, limit: int) -> list[LiteratureRecord]:
    records: list[LiteratureRecord] = []
    for match in re.finditer(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", page, re.I | re.S):
        href, text = match.groups()
        url = urllib.parse.urljoin(landing, html.unescape(href).strip())
        parsed = urllib.parse.urlparse(url)
        if parsed.netloc.casefold() not in {"oecd-nea.org", "www.oecd-nea.org"} or not parsed.path.casefold().endswith(".pdf"):
            continue
        title = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(text))).strip()
        title = title or PurePosixPath(parsed.path).stem.replace("-", " ")
        records.append(LiteratureRecord(
            title=title, literature_type="技术报告", publication_date=None, source="OECD-NEA",
            publisher="OECD Nuclear Energy Agency", publisher_url=landing, landing_page_url=landing,
            open_access_url=landing, pdf_url=url, pdf_source="OECD-NEA official publication index",
            metadata_sources=["OECD-NEA"], source_database="OECD-NEA", source_record_id=url,
            source_ids={"oecd_nea": url}, is_open_access=True, oa_status="open", raw={"landing_page": landing},
        ))
        if len(records) >= limit:
            break
    return records


def _fallback(query: str, landing: str, source: str, error: str | None = None) -> LiteratureRecord:
    record = LiteratureRecord(
        title=query, literature_type="技术报告", source=source, publisher="OECD Nuclear Energy Agency",
        publisher_url=landing, landing_page_url=landing, best_access_url=landing,
        metadata_sources=[source], source_database=source, notes="官方出版物索引解析失败，已降级为 landing page",
        raw={"landing_page": landing},
    )
    if error:
        record.raw["parse_error"] = error
    return record
