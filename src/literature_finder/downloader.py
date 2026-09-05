"""Opt-in downloader for records whose public OA permission was verified."""

from __future__ import annotations

import csv
import re
import time
from pathlib import Path

import requests

from .models import DownloadResult, LiteratureRecord
from .sources.base import HttpClient


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


class SafeDownloader:
    def __init__(self, *, timeout: float = 30.0, retries: int = 2, min_interval: float = 1.0, client: HttpClient | None = None) -> None:
        self.client = client or HttpClient(timeout=timeout, retries=retries, min_interval=min_interval)

    def download(self, records: list[LiteratureRecord], directory: str | Path, *, selected: set[int] | None = None, type_filter: set[str] | None = None) -> list[DownloadResult]:
        root = Path(directory)
        papers = root / "papers"
        papers.mkdir(parents=True, exist_ok=True)
        results: list[DownloadResult] = []
        for sequence, record in enumerate(records, 1):
            if selected is not None and sequence not in selected:
                continue
            if type_filter and (record.literature_type or "其他") not in type_filter:
                continue
            if not (record.download_permission_verified and record.download_url):
                results.append(DownloadResult(sequence, record.title, "skipped", source_url=record.best_access_url or "", failure_reason="not verified as legal OA"))
                continue
            filename = filename_for(sequence, record)
            target = papers / filename
            if target.exists() and target.stat().st_size > 0:
                results.append(DownloadResult(sequence, record.title, "already_exists", filename, record.download_url))
                continue
            try:
                response = self.client.request("GET", record.download_url, stream=True)
                content_type = (response.headers.get("Content-Type") or "").lower()
                first_chunk = next(response.iter_content(8192), b"")
                if not (first_chunk.startswith(b"%PDF") or "pdf" in content_type):
                    results.append(DownloadResult(sequence, record.title, "failed", filename, record.download_url, "response is not a PDF"))
                    continue
                with target.open("wb") as handle:
                    handle.write(first_chunk)
                    for chunk in response.iter_content(8192):
                        if chunk:
                            handle.write(chunk)
                if target.stat().st_size < 512:
                    target.unlink(missing_ok=True)
                    results.append(DownloadResult(sequence, record.title, "failed", filename, record.download_url, "file is unexpectedly small"))
                else:
                    results.append(DownloadResult(sequence, record.title, "downloaded", filename, record.download_url))
            except (requests.RequestException, RuntimeError, OSError) as exc:
                target.unlink(missing_ok=True)
                results.append(DownloadResult(sequence, record.title, "failed", filename, record.download_url, str(exc)))
            time.sleep(self.client.min_interval)
        write_report(results, root / "download_report.csv")
        return results


def filename_for(sequence: int, record: LiteratureRecord) -> str:
    author = record.authors[0].split()[-1] if record.authors else "document"
    year = (record.publication_date or "")[:4] or "unknown"
    stem = f"{sequence:03d}_{author}_{year}_{record.title}"
    stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", stem)
    stem = re.sub(r"\s+", " ", stem).strip(" .")
    return stem[:170] + ".pdf"


def write_report(results: list[DownloadResult], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["序号", "文献名", "状态", "文件名", "来源链接", "失败原因"])
        for result in results:
            writer.writerow([result.sequence, result.title, result.status, result.filename, result.source_url, result.failure_reason])

