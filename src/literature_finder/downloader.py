"""Backward-compatible downloader facade.

New integrations should import :class:`DownloadManager` from
``literature_finder.download``. The old ``SafeDownloader`` name remains
available so existing callers keep working.
"""

from __future__ import annotations

import re

from .download.manager import DownloadManager, write_report
from .models import LiteratureRecord


def parse_selection(spec: str, total: int) -> set[int]:
    selected: set[int] = set()
    for item in re.split(r"[,，\s]+", spec.strip()):
        if not item:
            continue
        if "-" in item:
            left, right = item.split("-", 1)
            if left.isdigit() and right.isdigit():
                selected.update(range(max(1, int(left)), min(total, int(right)) + 1))
        elif item.isdigit() and 1 <= int(item) <= total:
            selected.add(int(item))
    return selected


class SafeDownloader(DownloadManager):
    """Compatibility alias for the upgraded opt-in DownloadManager."""


def filename_for(sequence: int, record: LiteratureRecord) -> str:
    """Preserve the original public filename helper for existing clients."""
    author = record.authors[0].split()[-1] if record.authors else "document"
    year = str(record.year or (record.publication_date or "")[:4] or "unknown")
    stem = f"{sequence:03d}_{author}_{year}_{record.title}"
    stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", stem)
    stem = re.sub(r"\s+", " ", stem).strip(" .")
    return stem[:170] + ".pdf"


__all__ = ["DownloadManager", "SafeDownloader", "filename_for", "parse_selection", "write_report"]
