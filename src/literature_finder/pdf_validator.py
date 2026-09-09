"""PDF validation and hashing helpers used after download and during scans."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class PdfValidationResult:
    valid: bool
    reason: str = ""
    file_size: int = 0


def validate_pdf(path: str | Path, *, min_size: int = 256, parse: bool = True) -> PdfValidationResult:
    file = Path(path)
    try:
        size = file.stat().st_size
        if size < min_size:
            return PdfValidationResult(False, "file is unexpectedly small", size)
        with file.open("rb") as handle:
            header = handle.read(5)
        if header != b"%PDF-":
            return PdfValidationResult(False, "missing PDF header", size)
        if parse:
            try:
                from pypdf import PdfReader

                reader = PdfReader(str(file), strict=False)
                if not reader.pages:
                    return PdfValidationResult(False, "PDF has no readable pages", size)
            except Exception as exc:
                return PdfValidationResult(False, f"PDF parser rejected file: {exc}", size)
        return PdfValidationResult(True, "", size)
    except OSError as exc:
        return PdfValidationResult(False, str(exc), 0)


def is_valid_pdf(path: str | Path) -> bool:
    return validate_pdf(path, parse=False).valid


def sha256_file(path: str | Path, *, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()
