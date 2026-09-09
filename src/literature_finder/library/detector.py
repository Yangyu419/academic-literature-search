"""Pre-download local duplicate detection with conservative match rules."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
import re

from ..metadata import normalize_doi, normalize_record, normalize_title
from ..models import LiteratureRecord
from ..pdf_validator import validate_pdf
from .manifest import LiteratureManifest
from .scanner import LocalDocumentEntry, LocalDocumentIndex


@dataclass(slots=True)
class ExistingDocumentResult:
    exists: bool
    confidence: float = 0.0
    reason: str = ""
    matched_by: str = ""
    existing_path: str | None = None
    existing_sha256: str | None = None
    existing_record: LocalDocumentEntry | None = None


class LocalLibraryChecker:
    def __init__(self, root: str | Path, *, fuzzy_threshold: float = 0.95, manifest_path: str | Path | None = None) -> None:
        self.root = Path(root)
        self.fuzzy_threshold = fuzzy_threshold
        self.manifest = LiteratureManifest(manifest_path or self.root / "literature_manifest.json").load()
        self.index = LocalDocumentIndex(self.root)

    def refresh(self) -> LocalDocumentIndex:
        self.index.scan()
        for entry in self.index.entries:
            self.manifest.merge_scan(entry)
        # Reuse manifest metadata for files whose PDF metadata is sparse. The
        # filesystem scan remains authoritative for current file existence.
        indexed_paths = {entry.path.resolve() for entry in self.index.entries}
        for item in self.manifest.entries:
            raw_path = item.get("filepath") or ""
            path = Path(raw_path)
            if not path.is_absolute():
                path = self.root / path
            if not path.exists() or path.resolve() in indexed_paths:
                continue
            try:
                entry = LocalDocumentEntry(
                    path=path, filename=path.name, file_size=int(item.get("file_size") or path.stat().st_size),
                    sha256=str(item.get("sha256") or ""), doi=item.get("doi"), title=item.get("title"),
                    title_normalized=item.get("title_normalized"), first_author=item.get("first_author"),
                    year=item.get("year"), source_ids=item.get("source_ids") or {},
                )
                self.index.add(entry)
            except (OSError, TypeError, ValueError):
                continue
        self.manifest.save()
        return self.index

    def check(self, record: LiteratureRecord, *, target_path: Path | None = None) -> ExistingDocumentResult:
        normalize_record(record)
        if (match := self.index.find_by_doi(record.doi_normalized)):
            return self._result(match, 1.0, "Normalized DOI already exists in local library", "doi")
        if (match := self.index.find_by_source_ids(record.source_ids)):
            return self._result(match, 0.99, "Provider record ID already exists in local library", "source_id")
        title_key = record.title_normalized or normalize_title(record.title)
        for match in self.index.find_by_title(title_key):
            if _same_author_and_year(record, match):
                return self._result(match, 0.98, "Normalized title, author, and year match", "title_author_year")
        for match in self.index.entries:
            if not title_key or not match.title_normalized:
                continue
            similarity = SequenceMatcher(None, title_key, match.title_normalized).ratio()
            if similarity >= self.fuzzy_threshold and _same_author_and_year(record, match):
                return self._result(match, similarity, "Conservative fuzzy title match with author and year", "fuzzy_title")
        if target_path and target_path.exists():
            if validate_pdf(target_path).valid:
                entry = next((item for item in self.index.entries if item.path == target_path), None)
                return self._result(entry, 0.90, "Target filename already contains a valid PDF", "filename") if entry else ExistingDocumentResult(True, 0.90, "Target filename already contains a valid PDF", "filename", str(target_path))
            return ExistingDocumentResult(False, 0.0, "Target filename exists but is not a valid PDF", "filename_invalid", str(target_path))
        return ExistingDocumentResult(False)

    @staticmethod
    def _result(entry: LocalDocumentEntry | None, confidence: float, reason: str, matched_by: str) -> ExistingDocumentResult:
        return ExistingDocumentResult(True, confidence, reason, matched_by, str(entry.path) if entry else None, entry.sha256 if entry else None, entry)


def _same_author_and_year(record: LiteratureRecord, entry: LocalDocumentEntry) -> bool:
    record_author = _author_key(record.authors[0] if record.authors else "")
    entry_author = _author_key(entry.first_author or "")
    author_ok = not record_author or not entry_author or record_author == entry_author
    year_ok = record.year is None or entry.year is None or abs(record.year - entry.year) <= 1
    return author_ok and year_ok


def _author_key(value: str) -> str:
    parts = re.findall(r"[A-Za-z\u4e00-\u9fff]+", value.casefold())
    if not parts:
        return ""
    return parts[0] if "," in value else parts[-1]
