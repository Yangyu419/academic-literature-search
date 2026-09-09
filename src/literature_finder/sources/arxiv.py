"""arXiv Atom API adapter."""

from __future__ import annotations

import urllib.parse
import xml.etree.ElementTree as ET

from ..models import LiteratureRecord
from .base import HttpClient


class ArxivAdapter:
    name = "arXiv"
    atom = "http://www.w3.org/2005/Atom"

    def __init__(self, client: HttpClient | None = None) -> None:
        self.client = client or HttpClient(min_interval=3.0)

    def search(self, query: str, *, limit: int = 20) -> list[LiteratureRecord]:
        url = "https://export.arxiv.org/api/query?search_query=" + urllib.parse.quote("all:" + query) + f"&start=0&max_results={min(limit, 50)}"
        root = ET.fromstring(self.client.request("GET", url).content)
        output: list[LiteratureRecord] = []
        for entry in root.findall(f"{{{self.atom}}}entry"):
            title = " ".join((entry.findtext(f"{{{self.atom}}}title") or "").split())
            if not title:
                continue
            abs_url = entry.findtext(f"{{{self.atom}}}id")
            published = entry.findtext(f"{{{self.atom}}}published") or ""
            arxiv_id = abs_url.rsplit("/", 1)[-1] if abs_url else ""
            output.append(LiteratureRecord(
                title=title, literature_type="预印本", publication_date=published[:10] or None, source="arXiv",
                publisher_url=abs_url, open_access_url=abs_url, authors=[(a.findtext(f"{{{self.atom}}}name") or "") for a in entry.findall(f"{{{self.atom}}}author")],
                abstract=" ".join((entry.findtext(f"{{{self.atom}}}summary") or "").split()), metadata_sources=[self.name],
                is_downloadable=bool(arxiv_id), download_url=f"https://arxiv.org/pdf/{arxiv_id}" if arxiv_id else None,
                download_source="arXiv", download_file_type="pdf", download_permission_verified=bool(arxiv_id),
                source_database=self.name, source_record_id=arxiv_id,
                source_ids={"arxiv": arxiv_id} if arxiv_id else {}, landing_page_url=abs_url,
                is_open_access=bool(arxiv_id), oa_status="open" if arxiv_id else None, oa_version="submittedVersion",
                pdf_url=f"https://arxiv.org/pdf/{arxiv_id}" if arxiv_id else None, pdf_source="arXiv",
                raw={"arxiv_id": arxiv_id},
            ))
        return output
