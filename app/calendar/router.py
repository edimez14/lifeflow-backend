from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.calendar.schemas import CalendarCreate, CalendarResponse, CalendarUpdate
from app.calendar.service import (
    create_calendar,
    delete_calendar,
    get_calendar_by_id,
    list_calendars,
    update_calendar,
)
from app.database import get_db


router = APIRouter(
    prefix="/workspaces/{workspace_id}/calendars", tags=["calendar"])


@router.get("", response_model=list[CalendarResponse])
async def read_calendars(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[CalendarResponse]:
    """List calendars for one workspace."""

    calendars = await list_calendars(db, workspace_id)
    return [CalendarResponse.model_validate(calendar) for calendar in calendars]


@router.post("", response_model=CalendarResponse, status_code=status.HTTP_201_CREATED)
async def create_calendar_view(
    workspace_id: str,
    payload: CalendarCreate,
    db: AsyncSession = Depends(get_db),
) -> CalendarResponse:
    """Create one calendar in a workspace."""

    calendar = await create_calendar(db, workspace_id, payload)
    return CalendarResponse.model_validate(calendar)


@router.put("/{calendar_id}", response_model=CalendarResponse)
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


@router.delete("/{calendar_id}", status_code=status.HTTP_204_NO_CONTENT)
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
