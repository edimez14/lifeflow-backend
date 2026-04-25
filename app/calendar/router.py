from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.calendar.schemas import (
    CalendarCreate,
    CalendarResponse,
    CalendarUpdate,
    EventCreate,
    EventResponse,
    EventUpdate,
)
from app.calendar.service import (
    create_calendar,
    create_event,
    delete_calendar,
    delete_event,
    get_calendar_by_id,
    get_event_by_id,
    list_calendars,
    list_events,
    update_calendar,
    update_event,
)
from app.database import get_db


router = APIRouter(tags=["calendar"])


@router.get("/workspaces/{workspace_id}/calendars", response_model=list[CalendarResponse])
async def read_calendars(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[CalendarResponse]:
    """List calendars for one workspace."""

    calendars = await list_calendars(db, workspace_id)
    return [CalendarResponse.model_validate(calendar) for calendar in calendars]


@router.post("/workspaces/{workspace_id}/calendars", response_model=CalendarResponse, status_code=status.HTTP_201_CREATED)
async def create_calendar_view(
    workspace_id: str,
    payload: CalendarCreate,
    db: AsyncSession = Depends(get_db),
) -> CalendarResponse:
    """Create one calendar in a workspace."""

    calendar = await create_calendar(db, workspace_id, payload)
    return CalendarResponse.model_validate(calendar)


@router.put("/workspaces/{workspace_id}/calendars/{calendar_id}", response_model=CalendarResponse)
async def update_calendar_view(
    workspace_id: str,
    calendar_id: str,
    payload: CalendarUpdate,
    db: AsyncSession = Depends(get_db),
) -> CalendarResponse:
    """Update one workspace calendar."""

    calendar = await get_calendar_by_id(db, workspace_id, calendar_id)
    if calendar is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar not found",
        )
    updated_calendar = await update_calendar(db, calendar, payload)
    return CalendarResponse.model_validate(updated_calendar)


@router.delete("/workspaces/{workspace_id}/calendars/{calendar_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_calendar_view(
    workspace_id: str,
    calendar_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete one workspace calendar."""

    calendar = await get_calendar_by_id(db, workspace_id, calendar_id)
    if calendar is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar not found",
        )
    await delete_calendar(db, calendar)


@router.get("/workspaces/{workspace_id}/events", response_model=list[EventResponse])
async def read_events(
    workspace_id: str,
    start: datetime = Query(...),
    end: datetime = Query(...),
    db: AsyncSession = Depends(get_db),
) -> list[EventResponse]:
    """List workspace events in a date range including recurrences."""

    return await list_events(db, workspace_id, start, end)


@router.post("/workspaces/{workspace_id}/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event_view(
    workspace_id: str,
    payload: EventCreate,
    db: AsyncSession = Depends(get_db),
) -> EventResponse:
    """Create one workspace event."""

    try:
        event = await create_event(db, workspace_id, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return EventResponse.model_validate(event)


@router.put("/workspaces/{workspace_id}/events/{event_id}", response_model=EventResponse)
async def update_event_view(
    workspace_id: str,
    event_id: str,
    payload: EventUpdate,
    db: AsyncSession = Depends(get_db),
) -> EventResponse:
    """Update one workspace event."""

    event = await get_event_by_id(db, workspace_id, event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    updated_event = await update_event(db, event, payload)
    return EventResponse.model_validate(updated_event)


@router.delete("/workspaces/{workspace_id}/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event_view(
    workspace_id: str,
    event_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete one workspace event."""

    event = await get_event_by_id(db, workspace_id, event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    await delete_event(db, event)
