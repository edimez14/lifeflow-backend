from __future__ import annotations

from enum import Enum


class TaskPriority(str, Enum):
    """Priority options for a task."""

    URGENT = "urgent"
    IMPORTANT = "important"
    NORMAL = "normal"
    LOW = "low"


class TaskStatus(str, Enum):
    """Status options for a task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
