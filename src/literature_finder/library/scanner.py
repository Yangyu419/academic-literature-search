"""Scan local PDFs and extract conservative identifiers for duplicate checks."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

from ..metadata import normalize_doi, normalize_title, publication_year
from ..pdf_validator import validate_pdf

DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.I)


@dataclass(slots=True)
class LocalDocumentEntry:
    path: Path
    filename: str
    file_size: int
    sha256: str
    doi: str | None = None
    title: str | None = None
    title_normalized: str | None = None
    first_author: str | None = None
    year: int | None = None
    source_ids: dict[str, str] = field(default_factory=dict)


class LocalDocumentIndex:
    def __init__(self, root: str | Path, *, min_size: int = 256) -> None:
        self.root = Path(root)
        self.min_size = min_size
        self.entries: list[LocalDocumentEntry] = []
        self.by_doi: dict[str, LocalDocumentEntry] = {}
        self.by_source_id: dict[tuple[str, str], LocalDocumentEntry] = {}
        self.by_title: dict[str, list[LocalDocumentEntry]] = {}
        self.by_hash: dict[str, LocalDocumentEntry] = {}

    def scan(self) -> "LocalDocumentIndex":
        self.entries.clear()
        self.by_doi.clear(); self.by_source_id.clear(); self.by_title.clear(); self.by_hash.clear()
        if not self.root.exists():
            return self
        for path in sorted(self.root.rglob("*.pdf")):
            if any(part in {".download_tmp", ".cache"} for part in path.parts):
                continue
            try:
                if not path.is_file() or path.stat().st_size < self.min_size or not validate_pdf(path).valid:
                    continue
                entry = self._entry(path)
            except OSError:
                continue
            self.add(entry)
        return self

    def add(self, entry: LocalDocumentEntry) -> None:
        self.entries.append(entry)
        if entry.doi:
            self.by_doi.setdefault(entry.doi, entry)
        for provider, value in entry.source_ids.items():
            self.by_source_id.setdefault((provider.casefold(), str(value)), entry)
        if entry.title_normalized:
            self.by_title.setdefault(entry.title_normalized, []).append(entry)
        self.by_hash.setdefault(entry.sha256, entry)

    def find_by_doi(self, doi: str | None) -> LocalDocumentEntry | None:
        return self.by_doi.get(doi.casefold()) if doi else None

    def find_by_source_ids(self, source_ids: dict[str, str]) -> LocalDocumentEntry | None:
        for provider, value in source_ids.items():
            if value and (match := self.by_source_id.get((provider.casefold(), str(value)))):
                return match
        return None

    def find_by_title(self, title_normalized: str | None) -> list[LocalDocumentEntry]:
        return list(self.by_title.get(title_normalized or "", []))

    def find_by_hash(self, sha256: str | None) -> LocalDocumentEntry | None:
        return self.by_hash.get(sha256 or "")

    def _entry(self, path: Path) -> LocalDocumentEntry:
        data = path.read_bytes()
        sha256 = hashlib.sha256(data).hexdigest()
        text, metadata = _extract_pdf_text_and_metadata(path, data)
        metadata_text = " ".join(f"{key} {value}" for key, value in metadata.items())
        doi = normalize_doi(_find_doi(text) or _find_doi(metadata_text) or _find_doi(path.name))
        title = _extract_title(text) or _metadata_value(metadata, "title")
        author = _extract_first_author(text) or _metadata_value(metadata, "author")
        return LocalDocumentEntry(
            path=path, filename=path.name, file_size=len(data), sha256=sha256,
            doi=doi, title=title, title_normalized=normalize_title(title) if title else None,
            first_author=author, year=publication_year(text) or publication_year(metadata_text),
        )


def _extract_pdf_text_and_metadata(path: Path, data: bytes) -> tuple[str, dict[str, str]]:
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path), strict=False)
        text = "\n".join((page.extract_text() or "") for page in reader.pages[:2])[:20000]
        metadata = {str(key): str(value) for key, value in (reader.metadata or {}).items() if value}
        return text, metadata
    except Exception:
        return data[:20000].decode("utf-8", errors="ignore"), {}


def _metadata_value(metadata: dict[str, str], field: str) -> str | None:
    for key, value in metadata.items():
        if key.casefold().lstrip("/") == field.casefold():
            return value.strip() or None
    return None


def _find_doi(text: str) -> str | None:
    match = DOI_RE.search(text or "")
    return match.group(0).rstrip(".,;)") if match else None


def _extract_title(text: str) -> str | None:
    lines = [re.sub(r"\s+", " ", line).strip(" \t\r\n") for line in (text or "").splitlines()]
    for line in lines[:40]:
        if 20 <= len(line) <= 240 and not re.search(r"^(abstract|keywords?|doi|http|copyright)\b", line, re.I):
            return line
    return None


def _extract_first_author(text: str) -> str | None:
    for line in (text or "").splitlines()[:50]:
        if re.search(r"\b(and|et al\.|作者|authors?)\b", line, re.I):
            words = re.findall(r"[A-Z][A-Za-z'’-]{2,}", line)
            return words[0] if words else None
    return None
