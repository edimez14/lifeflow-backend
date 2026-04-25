from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CalendarBase(BaseModel):
    """Shared calendar fields."""

    name: str
    color: str
    active: bool = True


class CalendarCreate(CalendarBase):
    """Data used to create a calendar."""


class CalendarUpdate(BaseModel):
    """Data used to update a calendar."""

    name: str | None = None
    color: str | None = None
    active: bool | None = None


class CalendarResponse(CalendarBase):
    """Calendar data returned by API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str


class EventBase(BaseModel):
    """Shared event fields."""

    title: str
    description: str | None = None
    start_datetime: datetime
    end_datetime: datetime
    recurrence_rule: str | None = None
    color: str | None = None
    category: str | None = None
    is_exception: bool = False
    parent_event_id: str | None = None


class EventCreate(EventBase):
    """Data used to create an event."""

    calendar_id: str


class EventUpdate(BaseModel):
    """Data used to update an event."""

    title: str | None = None
    description: str | None = None
    start_datetime: datetime | None = None
    end_datetime: datetime | None = None
    recurrence_rule: str | None = None
    color: str | None = None
    category: str | None = None
    is_exception: bool | None = None
    parent_event_id: str | None = None


class EventResponse(EventBase):
    """Event data returned by API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    calendar_id: str


# ---------- Monthly Goals ----------

class MonthlyGoalBase(BaseModel):
    """Shared monthly goal fields."""

    year: int
    month: int
    goal_text: str
    action_plan: str


class MonthlyGoalCreate(MonthlyGoalBase):
    """Data used to create or update a monthly goal."""


class MonthlyGoalResponse(MonthlyGoalBase):
    """Monthly goal returned by API. Fields id and workspace_id are None when no goal exists yet."""

    model_config = ConfigDict(from_attributes=True)

    id: str | None = None
    workspace_id: str | None = None
