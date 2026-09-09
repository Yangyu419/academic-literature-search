"""Lawful academic literature search and Excel export toolkit."""

from .download import DownloadManager
from .library import ExistingDocumentResult, LocalLibraryChecker, LiteratureManifest
from .models import LiteratureRecord, ResearchRequest, SearchPlan
from .state_machine import TaskState, TaskStateMachine

__all__ = [
    "DownloadManager", "ExistingDocumentResult", "LiteratureManifest", "LocalLibraryChecker",
    "LiteratureRecord", "ResearchRequest", "SearchPlan", "TaskState", "TaskStateMachine",
]
__version__ = "0.2.0"
