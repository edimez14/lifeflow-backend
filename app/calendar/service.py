from __future__ import annotations

from datetime import datetime

from dateutil.rrule import rrulestr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.calendar.models import Calendar, Event, MonthlyGoal
from app.calendar.schemas import (
    CalendarCreate,
    CalendarUpdate,
    EventCreate,
    EventResponse,
    EventUpdate,
    MonthlyGoalCreate,
    MonthlyGoalResponse,
)


async def list_calendars(db: AsyncSession, workspace_id: str) -> list[Calendar]:
    """Return all calendars for one workspace."""

    result = await db.execute(
        select(Calendar)
        .where(Calendar.workspace_id == workspace_id)
        .order_by(Calendar.name.asc())
    )
    return list(result.scalars().all())


async def get_calendar_by_id(
    db: AsyncSession,
    workspace_id: str,
    calendar_id: str,
) -> Calendar | None:
    """Return one workspace calendar by id."""

    result = await db.execute(
        select(Calendar).where(
            Calendar.workspace_id == workspace_id,
            Calendar.id == calendar_id,
        )
    )
    return result.scalar_one_or_none()


async def create_calendar(
    db: AsyncSession,
    workspace_id: str,
    payload: CalendarCreate,
) -> Calendar:
    """Create one calendar inside a workspace."""

    calendar = Calendar(
        workspace_id=workspace_id,
        **payload.model_dump(),
    )
    db.add(calendar)
    await db.commit()
    await db.refresh(calendar)
    return calendar


async def update_calendar(
    db: AsyncSession,
    calendar: Calendar,
    payload: CalendarUpdate,
) -> Calendar:
    """Update one calendar."""

    update_data = payload.model_dump(exclude_unset=True)
    for field_name, value in update_data.items():
        setattr(calendar, field_name, value)

    await db.commit()
    await db.refresh(calendar)
    return calendar


async def delete_calendar(db: AsyncSession, calendar: Calendar) -> None:
    """Delete one calendar."""

    await db.delete(calendar)
    await db.commit()


async def create_event(
    db: AsyncSession,
    workspace_id: str,
    payload: EventCreate,
) -> Event:
    """Create one event in a workspace calendar."""

    calendar = await db.scalar(
        select(Calendar).where(
            Calendar.id == payload.calendar_id,
            Calendar.workspace_id == workspace_id,
        )
    )
    if calendar is None:
        raise ValueError("Calendar not found")

    event_data = payload.model_dump()
    event = Event(**event_data)
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


async def get_event_by_id(
    db: AsyncSession,
    workspace_id: str,
    event_id: str,
) -> Event | None:
    """Return one workspace event by id."""

    result = await db.execute(
        select(Event)
        .join(Calendar, Calendar.id == Event.calendar_id)
        .where(
            Calendar.workspace_id == workspace_id,
            Event.id == event_id,
        )
    )
    return result.scalar_one_or_none()


async def update_event(
    db: AsyncSession,
    event: Event,
    payload: EventUpdate,
) -> Event:
    """Update one event."""

    update_data = payload.model_dump(exclude_unset=True)
    for field_name, value in update_data.items():
        setattr(event, field_name, value)

    await db.commit()
    await db.refresh(event)
    return event


async def delete_event(db: AsyncSession, event: Event) -> None:
    """Delete one event."""

    await db.delete(event)
    await db.commit()


def _in_range(
    start_datetime: datetime,
    end_datetime: datetime,
    range_start: datetime,
    range_end: datetime,
) -> bool:
    """Check if one event instance overlaps a range."""

    return start_datetime <= range_end and end_datetime >= range_start


def expand_event_occurrences(
    event: Event,
    range_start: datetime,
    range_end: datetime,
    exceptions_by_date: dict[datetime, Event] | None = None,
) -> list[EventResponse]:
    """
    Expand the recurrence rule of a single event into concrete instances.

    If exceptions exist for a date the exception replaces the occurrence.
    Non‑recurring events are returned as a single‑element list when they overlap
    the requested range.
    """
    occurrences: list[EventResponse] = []

    if not event.recurrence_rule:
        if _in_range(event.start_datetime, event.end_datetime, range_start, range_end):
            occurrences.append(EventResponse.model_validate(event))
        return occurrences

    exceptions = exceptions_by_date or {}
    duration = event.end_datetime - event.start_datetime
    rule = rrulestr(event.recurrence_rule, dtstart=event.start_datetime)
    instance_starts = rule.between(range_start, range_end, inc=True)

    for start in instance_starts:
        replacement = exceptions.get(start)
        if replacement is not None:
            occurrences.append(EventResponse.model_validate(replacement))
            continue

        end = start + duration
        occurrences.append(
            EventResponse(
                id=f"{event.id}:{int(start.timestamp())}",
                calendar_id=event.calendar_id,
                title=event.title,
                description=event.description,
                start_datetime=start,
                end_datetime=end,
                recurrence_rule=event.recurrence_rule,
                color=event.color,
                category=event.category,
                is_exception=False,
                parent_event_id=event.id,
            )
        )

    return occurrences


async def list_events(
    db: AsyncSession,
    workspace_id: str,
    start_datetime: datetime,
    end_datetime: datetime,
) -> list[EventResponse]:
    """List events in a range, expanding recurrence rules when needed."""

    result = await db.execute(
        select(Event)
        .join(Calendar, Calendar.id == Event.calendar_id)
        .where(Calendar.workspace_id == workspace_id)
    )
    all_events = list(result.scalars().all())

    exceptions_by_parent: dict[str, dict[datetime, Event]] = {}
    for event in all_events:
        if event.is_exception and event.parent_event_id:
            parent_exceptions = exceptions_by_parent.setdefault(
                event.parent_event_id, {}
            )
            parent_exceptions[event.start_datetime] = event

    responses: list[EventResponse] = []
    for event in all_events:
        if event.is_exception:
            continue

        exceptions = exceptions_by_parent.get(event.id, {})
        responses.extend(
            expand_event_occurrences(
                event, start_datetime, end_datetime, exceptions)
        )

    responses.sort(key=lambda item: item.start_datetime)
    return responses


# ---------- Monthly Goals ----------

async def get_monthly_goal(
    db: AsyncSession,
    workspace_id: str,
    year: int,
    month: int,
) -> MonthlyGoal | None:
    """Return the monthly goal for a given workspace, year, and month."""

    result = await db.execute(
        select(MonthlyGoal).where(
            MonthlyGoal.workspace_id == workspace_id,
            MonthlyGoal.year == year,
            MonthlyGoal.month == month,
        )
    )
    return result.scalar_one_or_none()


async def upsert_monthly_goal(
    db: AsyncSession,
    workspace_id: str,
    year: int,
    month: int,
    payload: MonthlyGoalCreate,
) -> MonthlyGoal:
    """Create or update the monthly goal for a workspace and month."""

    existing = await get_monthly_goal(db, workspace_id, year, month)
    if existing is not None:
        existing.goal_text = payload.goal_text
        existing.action_plan = payload.action_plan
        await db.commit()
        await db.refresh(existing)
        return existing

    new_goal = MonthlyGoal(
        workspace_id=workspace_id,
        year=year,
        month=month,
        goal_text=payload.goal_text,
        action_plan=payload.action_plan,
    )
    db.add(new_goal)
    await db.commit()
    await db.refresh(new_goal)
    return new_goal


async def list_monthly_goals(
    db: AsyncSession,
    workspace_id: str,
) -> list[MonthlyGoal]:
    """Return all monthly goals for a workspace, ordered by year desc, month desc."""
    result = await db.execute(
        select(MonthlyGoal)
        .where(MonthlyGoal.workspace_id == workspace_id)
        .order_by(MonthlyGoal.year.desc(), MonthlyGoal.month.desc())
    )
    return list(result.scalars().all())


async def delete_monthly_goal(
    db: AsyncSession,
    workspace_id: str,
    year: int,
    month: int,
) -> bool:
    """Delete a monthly goal. Returns True if deleted, False if not found."""
    goal = await get_monthly_goal(db, workspace_id, year, month)
    if goal is None:
        return False
    await db.delete(goal)
    await db.commit()
    return True
