"""Local literature indexing and duplicate detection."""

from .detector import ExistingDocumentResult, LocalLibraryChecker
from .manifest import LiteratureManifest
from .scanner import LocalDocumentEntry, LocalDocumentIndex

__all__ = [
    "ExistingDocumentResult", "LocalDocumentEntry", "LocalDocumentIndex",
    "LocalLibraryChecker", "LiteratureManifest",
]
