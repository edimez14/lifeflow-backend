from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.timer.types import TimerStatus


class TimerStartRequest(BaseModel):
    """Data to start a new timer session."""

    task_id: str | None = None
    estimated_seconds: int = 0


class TimerUpdateData(BaseModel):
    """Optional fields that can be updated mid-session."""

    estimated_seconds: int | None = None


class TimerResponse(BaseModel):
    """Timer session data returned by API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: str | None
    workspace_id: str
    estimated_seconds: int
    actual_seconds: int
    status: TimerStatus
    started_at: datetime
    finished_at: datetime | None
    paused_at: datetime | None


class TimerHistoryItem(BaseModel):
    """Single timer session shown in history."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    estimated_seconds: int
    actual_seconds: int
    status: TimerStatus
    started_at: datetime
    finished_at: datetime | None
    task_id: str | None
