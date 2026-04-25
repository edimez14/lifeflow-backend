from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.calendar.models import Calendar
from app.calendar.schemas import CalendarCreate, CalendarUpdate


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
