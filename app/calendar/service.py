from __future__ import annotations

from datetime import datetime

from dateutil.rrule import rrulestr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.calendar.models import Calendar, Event
from app.calendar.schemas import (
    CalendarCreate,
    CalendarUpdate,
    EventCreate,
    EventResponse,
    EventUpdate,
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
                event.parent_event_id, {})
            parent_exceptions[event.start_datetime] = event

    responses: list[EventResponse] = []
    for event in all_events:
        if event.is_exception:
            if _in_range(
                event.start_datetime,
                event.end_datetime,
                start_datetime,
                end_datetime,
            ):
                responses.append(EventResponse.model_validate(event))
            continue

        if not event.recurrence_rule:
            if _in_range(
                event.start_datetime,
                event.end_datetime,
                start_datetime,
                end_datetime,
            ):
                responses.append(EventResponse.model_validate(event))
            continue

        duration = event.end_datetime - event.start_datetime
        recurrence = rrulestr(event.recurrence_rule,
                              dtstart=event.start_datetime)
        occurrences = recurrence.between(
            start_datetime, end_datetime, inc=True)
        parent_exceptions = exceptions_by_parent.get(event.id, {})

        for occurrence_start in occurrences:
            replacement_event = parent_exceptions.get(occurrence_start)
            if replacement_event is not None:
                responses.append(
                    EventResponse.model_validate(replacement_event))
                continue

            occurrence_end = occurrence_start + duration
            responses.append(
                EventResponse(
                    id=f"{event.id}:{int(occurrence_start.timestamp())}",
                    calendar_id=event.calendar_id,
                    title=event.title,
                    description=event.description,
                    start_datetime=occurrence_start,
                    end_datetime=occurrence_end,
                    recurrence_rule=event.recurrence_rule,
                    color=event.color,
                    category=event.category,
                    is_exception=False,
                    parent_event_id=event.id,
                )
            )

    responses.sort(key=lambda item: item.start_datetime)
    return responses
