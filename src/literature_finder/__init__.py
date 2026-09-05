"""Lawful academic literature search and Excel export toolkit."""

from .models import LiteratureRecord, ResearchRequest, SearchPlan
from .state_machine import TaskState, TaskStateMachine

__all__ = ["LiteratureRecord", "ResearchRequest", "SearchPlan", "TaskState", "TaskStateMachine"]
__version__ = "0.1.0"
