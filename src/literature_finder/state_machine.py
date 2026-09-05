"""Small workflow guard preventing accidental downloads before Excel export."""

from __future__ import annotations

from enum import StrEnum


class TaskState(StrEnum):
    INPUT = "INPUT"
    CLARIFICATION_CHECK = "CLARIFICATION_CHECK"
    WAITING_FOR_CLARIFICATION = "WAITING_FOR_CLARIFICATION"
    QUERY_PLANNING = "QUERY_PLANNING"
    SEARCHING = "SEARCHING"
    METADATA_VALIDATION = "METADATA_VALIDATION"
    DEDUPLICATION = "DEDUPLICATION"
    RANKING = "RANKING"
    LINK_RESOLUTION = "LINK_RESOLUTION"
    EXCEL_EXPORT = "EXCEL_EXPORT"
    WAITING_FOR_DOWNLOAD_SELECTION = "WAITING_FOR_DOWNLOAD_SELECTION"
    DOWNLOADING = "DOWNLOADING"
    COMPLETE = "COMPLETE"


class InvalidTransition(RuntimeError):
    """Raised when a workflow tries to skip a required safety gate."""


class TaskStateMachine:
    def __init__(self) -> None:
        self.state = TaskState.INPUT

    def transition(self, target: TaskState) -> TaskState:
        allowed = {
            TaskState.INPUT: {TaskState.CLARIFICATION_CHECK},
            TaskState.CLARIFICATION_CHECK: {TaskState.WAITING_FOR_CLARIFICATION, TaskState.QUERY_PLANNING},
            TaskState.WAITING_FOR_CLARIFICATION: {TaskState.QUERY_PLANNING, TaskState.COMPLETE},
            TaskState.QUERY_PLANNING: {TaskState.SEARCHING},
            TaskState.SEARCHING: {TaskState.METADATA_VALIDATION},
            TaskState.METADATA_VALIDATION: {TaskState.DEDUPLICATION},
            TaskState.DEDUPLICATION: {TaskState.RANKING},
            TaskState.RANKING: {TaskState.LINK_RESOLUTION},
            TaskState.LINK_RESOLUTION: {TaskState.EXCEL_EXPORT},
            TaskState.EXCEL_EXPORT: {TaskState.WAITING_FOR_DOWNLOAD_SELECTION, TaskState.COMPLETE},
            TaskState.WAITING_FOR_DOWNLOAD_SELECTION: {TaskState.DOWNLOADING, TaskState.COMPLETE},
            TaskState.DOWNLOADING: {TaskState.COMPLETE},
            TaskState.COMPLETE: set(),
        }
        if target not in allowed[self.state]:
            raise InvalidTransition(f"cannot transition from {self.state} to {target}")
        self.state = target
        return self.state

    def begin_download(self) -> TaskState:
        if self.state != TaskState.WAITING_FOR_DOWNLOAD_SELECTION:
            raise InvalidTransition("explicit user download selection is required after Excel export")
        return self.transition(TaskState.DOWNLOADING)

