from __future__ import annotations

from enum import Enum


class TimerStatus(str, Enum):
    """Possible states for a timer session."""

    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
