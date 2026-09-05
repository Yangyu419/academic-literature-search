import pytest

from literature_finder.state_machine import InvalidTransition, TaskState, TaskStateMachine


def test_download_requires_export_and_selection():
    machine = TaskStateMachine()
    with pytest.raises(InvalidTransition):
        machine.begin_download()
    for state in [TaskState.CLARIFICATION_CHECK, TaskState.QUERY_PLANNING, TaskState.SEARCHING, TaskState.METADATA_VALIDATION, TaskState.DEDUPLICATION, TaskState.RANKING, TaskState.LINK_RESOLUTION, TaskState.EXCEL_EXPORT, TaskState.WAITING_FOR_DOWNLOAD_SELECTION]:
        machine.transition(state)
    assert machine.begin_download() == TaskState.DOWNLOADING

