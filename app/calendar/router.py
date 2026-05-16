from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.calendar.models import CATEGORY_COLORS
from app.calendar.schemas import (
    CalendarCreate,
    CalendarResponse,
    CalendarUpdate,
    EventCategory,
    EventCreate,
    EventResponse,
    EventUpdate,
    MonthlyGoalCreate,
    MonthlyGoalResponse,
)
from app.calendar.service import (
    create_calendar,
    create_event,
    delete_calendar,
    delete_event,
    get_calendar_by_id,
    get_event_by_id,
    get_monthly_goal,
    list_calendars,
    list_events,
    update_calendar,
    update_event,
    upsert_monthly_goal,
)
from app.database import get_db
from app.websocket_manager import ConnectionManager, get_connection_manager


router = APIRouter(tags=["calendar"])


@router.get("/event-categories")
async def read_event_categories() -> list[dict]:
    """Lista las categorias disponibles para eventos con sus colores."""
    return [
        {
            "value": cat.value,
            "label": cat.name.replace("_", " ").title(),
            "color": CATEGORY_COLORS[cat],
        }
        for cat in EventCategory
    ]


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
    manager: ConnectionManager = Depends(get_connection_manager),
) -> EventResponse:
    """Create one workspace event."""

    try:
        event = await create_event(db, workspace_id, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    await manager.broadcast(
        workspace_id,
        {
            "type": "event.created",
            "data": EventResponse.model_validate(event).model_dump(mode="json"),
        },
    )
    return EventResponse.model_validate(event)


@router.put("/workspaces/{workspace_id}/events/{event_id}", response_model=EventResponse)
async def update_event_view(
    workspace_id: str,
    event_id: str,
    payload: EventUpdate,
    db: AsyncSession = Depends(get_db),
    manager: ConnectionManager = Depends(get_connection_manager),
) -> EventResponse:
    """Update one workspace event."""

    event = await get_event_by_id(db, workspace_id, event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    updated_event = await update_event(db, event, payload)
    await manager.broadcast(
        workspace_id,
        {
            "type": "event.updated",
            "data": EventResponse.model_validate(updated_event).model_dump(mode="json"),
        },
    )
    return EventResponse.model_validate(updated_event)


@router.delete("/workspaces/{workspace_id}/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event_view(
    workspace_id: str,
    event_id: str,
    db: AsyncSession = Depends(get_db),
    manager: ConnectionManager = Depends(get_connection_manager),
) -> None:
    """Delete one workspace event."""

    event = await get_event_by_id(db, workspace_id, event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    await delete_event(db, event)
    await manager.broadcast(
        workspace_id,
        {
            "type": "event.deleted",
            "data": {"id": event_id},
        },
    )


# ---------- Monthly Goals ----------

@router.get(
    "/workspaces/{workspace_id}/monthly-goals/{year}/{month}",
    response_model=MonthlyGoalResponse,
)
async def read_monthly_goal(
    workspace_id: str,
    year: int,
    month: int,
    db: AsyncSession = Depends(get_db),
) -> MonthlyGoalResponse:
    """Get the monthly goal for a workspace and month. Returns empty fields if none exists."""

    goal = await get_monthly_goal(db, workspace_id, year, month)
    if goal is not None:
        return MonthlyGoalResponse.model_validate(goal)
    # Return a placeholder with the requested year/month
    return MonthlyGoalResponse(
        year=year,
        month=month,
        goal_text="",
        action_plan="",
    )


@router.put(
    "/workspaces/{workspace_id}/monthly-goals/{year}/{month}",
    response_model=MonthlyGoalResponse,
)
async def put_monthly_goal(
    workspace_id: str,
    year: int,
    month: int,
    payload: MonthlyGoalCreate,
    db: AsyncSession = Depends(get_db),
) -> MonthlyGoalResponse:
    """Create or update the monthly goal for a workspace and month."""

    goal = await upsert_monthly_goal(db, workspace_id, year, month, payload)
    return MonthlyGoalResponse.model_validate(goal)
