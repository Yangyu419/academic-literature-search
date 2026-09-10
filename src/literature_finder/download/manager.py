"""Download manager with preflight local deduplication and post-download hash checks."""

from __future__ import annotations

import csv
import os
import re
import time
import uuid
from pathlib import Path

import requests

from ..library import LocalLibraryChecker
from ..models import DownloadResult, LiteratureRecord
from ..oa_rescue import OpenAccessRescue
from ..pdf_validator import sha256_file, validate_pdf
from ..sources.base import HttpClient


class DownloadManager:
    """Download public PDF candidates with local preflight and fallback."""

    def __init__(self, *, timeout: float = 30.0, retries: int = 2, min_interval: float = 1.0, client: HttpClient | None = None, fuzzy_threshold: float = 0.95, oa_rescue: OpenAccessRescue | None = None) -> None:
        self.client = client or HttpClient(timeout=timeout, retries=retries, min_interval=min_interval)
        self.fuzzy_threshold = fuzzy_threshold
        self.oa_rescue = oa_rescue

    def download(
        self,
        records: list[LiteratureRecord],
        directory: str | Path,
        *,
        selected: set[int] | None = None,
        type_filter: set[str] | None = None,
        relevance_threshold: float | None = None,
        start_year: int | None = None,
        end_year: int | None = None,
        force_redownload: bool = False,
    ) -> list[DownloadResult]:
        root = Path(directory)
        pdf_dir = root / "pdf"
        temporary_dir = root / ".download_tmp"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        temporary_dir.mkdir(parents=True, exist_ok=True)
        checker = LocalLibraryChecker(root, fuzzy_threshold=self.fuzzy_threshold)
        # This scan happens once, before the first possible HTTP request.
        checker.refresh()
        results: list[DownloadResult] = []
        for sequence, record in enumerate(records, 1):
            if selected is not None and sequence not in selected:
                continue
            if type_filter and (record.literature_type or "其他") not in type_filter:
                continue
            if relevance_threshold is not None and (record.relevance_score or 0) < relevance_threshold:
                continue
            if start_year is not None and (record.year or 0) < start_year:
                continue
            if end_year is not None and (record.year or 9999) > end_year:
                continue

            filename = filename_for(sequence, record)
            target = pdf_dir / filename
            if not force_redownload:
                existing = checker.check(record, target_path=target)
                if existing.exists:
                    _mark_existing(record, existing)
                    result = DownloadResult(sequence, record.title, "skipped_existing", filename, record.download_url or record.best_legal_access_url or "", existing.reason)
                    results.append(result)
                    continue
                if existing.matched_by == "filename_invalid":
                    _mark_error(record, "failed", existing.reason)
                    results.append(DownloadResult(sequence, record.title, "failed", filename, record.download_url or "", existing.reason))
                    continue

            if not (record.download_permission_verified and record.download_url) and record.doi:
                (self.oa_rescue or OpenAccessRescue()).rescue(record)

            candidates = _download_candidates(record)
            if not candidates:
                record.download_status = "unavailable"
                record.download_error = "no public PDF candidate"
                results.append(DownloadResult(sequence, record.title, "unavailable", filename, record.best_legal_access_url or record.best_access_url or "", record.download_error))
                continue

            record.download_status = "downloading"
            errors: list[str] = []
            for candidate in candidates:
                url = str(candidate["url"])
                record.download_url = url
                temp = temporary_dir / f"{uuid.uuid4().hex}.part"
                try:
                    response = self.client.request("GET", url, stream=True)
                    content_type = (response.headers.get("Content-Type") or "").casefold()
                    with temp.open("wb") as handle:
                        for chunk in response.iter_content(1024 * 64):
                            if chunk:
                                handle.write(chunk)
                    response.close()
                    if "text/html" in content_type:
                        raise DownloadError("response Content-Type is HTML")
                    validation = validate_pdf(temp)
                    if not validation.valid:
                        raise DownloadError(f"invalid PDF: {validation.reason}")
                    digest = sha256_file(temp)
                    duplicate = checker.index.find_by_hash(digest)
                    if duplicate:
                        record.download_status = "skipped_duplicate"
                        record.existing_local_copy = True
                        record.existing_local_path = str(duplicate.path.resolve())
                        record.duplicate_reason = "SHA256 matches an existing local PDF"
                        record.file_hash_sha256 = digest
                        checker.manifest.update_record(record, duplicate.path, digest)
                        checker.manifest.save()
                        results.append(DownloadResult(sequence, record.title, "skipped_duplicate", filename, url, record.duplicate_reason))
                        break
                    if target.exists():
                        raise DownloadError("target path appeared after preflight; refusing to overwrite")
                    os.replace(temp, target)
                    record.download_status = "downloaded"
                    record.download_path = str(target.resolve())
                    record.file_hash_sha256 = digest
                    entry = checker.index._entry(target)
                    checker.index.add(entry)
                    checker.manifest.update_record(record, target, digest)
                    checker.manifest.save()
                    results.append(DownloadResult(sequence, record.title, "downloaded", filename, url))
                    break
                except (requests.RequestException, RuntimeError, OSError, DownloadError) as exc:
                    errors.append(f"{url}: {exc}")
                finally:
                    temp.unlink(missing_ok=True)
                    time.sleep(self.client.min_interval)
            else:
                record.download_status = "failed"
                record.download_error = " ; ".join(errors)
                results.append(DownloadResult(sequence, record.title, "failed", filename, record.download_url or "", record.download_error))
        write_report(results, root / "download_report.csv")
        return results


class DownloadError(RuntimeError):
    pass


def _download_candidates(record: LiteratureRecord) -> list[dict[str, object]]:
    raw = record.raw.get("download_candidates")
    candidates: list[dict[str, object]] = []
    seen: set[str] = set()
    for item in raw if isinstance(raw, list) else []:
        if not isinstance(item, dict) or not item.get("url"):
            continue
        url = str(item["url"])
        if url not in seen:
            candidates.append(item)
            seen.add(url)
    if record.download_permission_verified and record.download_url and record.download_url not in seen:
        candidates.append({"url": record.download_url, "priority": 50, "source": record.download_source or "source-provided candidate", "file_type": record.download_file_type or "pdf"})
    candidates.sort(key=lambda item: int(item.get("priority", 50)))
    return candidates


def filename_for(sequence: int, record: LiteratureRecord) -> str:
    author = record.authors[0].split()[-1] if record.authors else "document"
    year = str(record.year or (record.publication_date or "")[:4] or "unknown")
    stem = f"{sequence:03d}_{year}_{author}_{record.title}"
    stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", stem)
    stem = re.sub(r"\s+", " ", stem).strip(" .")
    return stem[:170] + ".pdf"


def _mark_existing(record: LiteratureRecord, existing) -> None:
    record.download_status = "skipped_existing"
    record.existing_local_copy = True
    record.existing_local_path = str(Path(existing.existing_path).resolve()) if existing.existing_path else None
    record.duplicate_reason = existing.reason
    record.file_hash_sha256 = existing.existing_sha256


def _mark_error(record: LiteratureRecord, status: str, error: str) -> None:
    record.download_status = status
    record.download_error = error


def write_report(results: list[DownloadResult], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["序号", "文献名", "状态", "文件名", "来源链接", "失败原因"])
        for result in results:
            writer.writerow([result.sequence, result.title, result.status, result.filename, result.source_url, result.failure_reason])
