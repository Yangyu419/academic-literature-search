"""Persistent JSON manifest for local literature provenance."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from ..metadata import normalize_doi, normalize_title
from ..models import LiteratureRecord
from .scanner import LocalDocumentEntry


class LiteratureManifest:
    VERSION = 1

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.entries: list[dict[str, Any]] = []

    def load(self) -> "LiteratureManifest":
        if not self.path.exists():
            return self
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.entries = list(data.get("entries", [])) if isinstance(data, dict) else []
        except (OSError, ValueError, TypeError):
            self.entries = []
        return self

    def save(self) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": self.VERSION, "entries": self.entries}
        fd, temporary = tempfile.mkstemp(prefix="manifest_", suffix=".json", dir=self.path.parent)
        os.close(fd)
        temp_path = Path(temporary)
        try:
            temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(temp_path, self.path)
        finally:
            temp_path.unlink(missing_ok=True)
        return self.path

    def merge_scan(self, entry: LocalDocumentEntry) -> None:
        key = entry.doi or entry.title_normalized or entry.sha256
        existing = next((item for item in self.entries if _entry_key(item) == key), None)
        value = {
            "doi": entry.doi, "title": entry.title, "title_normalized": entry.title_normalized,
            "first_author": entry.first_author, "year": entry.year,
            "source_ids": entry.source_ids, "filename": entry.filename,
            "filepath": str(entry.path), "sha256": entry.sha256, "file_size": entry.file_size,
        }
        if existing is None:
            self.entries.append(value)
        else:
            existing.update({k: v for k, v in value.items() if v not in (None, "", {})})

    def update_record(self, record: LiteratureRecord, path: Path, sha256: str) -> None:
        record_doi = normalize_doi(record.doi)
        record_title = normalize_title(record.title)
        entry = {
            "doi": record_doi, "title": record.title, "title_normalized": record_title,
            "first_author": record.authors[0] if record.authors else None, "year": record.year,
            "source_ids": record.source_ids or record.external_ids, "filename": path.name,
            "filepath": str(path), "sha256": sha256, "file_size": path.stat().st_size,
            "downloaded_at": datetime.now().isoformat(timespec="seconds"),
            "source_url": record.download_url, "pdf_source": record.pdf_source or record.download_source,
        }
        key = record_doi or record_title
        existing = next((item for item in self.entries if _entry_key(item) == key), None)
        if existing is None:
            self.entries.append(entry)
        else:
            existing.update(entry)


def _entry_key(item: dict[str, Any]) -> str:
    return normalize_doi(item.get("doi")) or item.get("title_normalized") or item.get("sha256") or ""
