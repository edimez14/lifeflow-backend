from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.scheduler import remove_timer_job, schedule_timer_finish
from app.timer.models import TimerSession
from app.timer.schemas import TimerStartRequest
from app.timer.types import TimerStatus


def _ensure_aware(dt: datetime) -> datetime:
    """Ensure datetime is timezone-aware (UTC if naive)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


async def start_timer(
    db: AsyncSession, workspace_id: str, payload: TimerStartRequest
) -> TimerSession:
    """Create a new timer session and schedule its finish job."""

    now = datetime.now(UTC)
    timer = TimerSession(
        task_id=payload.task_id,
        workspace_id=workspace_id,
        estimated_seconds=payload.estimated_seconds,
        actual_seconds=0,
        status=TimerStatus.RUNNING,
        started_at=now,
    )
    db.add(timer)
    await db.commit()
    await db.refresh(timer)

    if timer.estimated_seconds > 0:
        finish_at = now + timedelta(seconds=timer.estimated_seconds)
        await schedule_timer_finish(
            timer_id=timer.id,
            workspace_id=workspace_id,
            run_at=finish_at,
            task_id=payload.task_id,
        )

    return timer


async def pause_timer(
    db: AsyncSession, workspace_id: str, timer_id: str
) -> TimerSession:
    """Pause a running timer and cancel its APScheduler job."""

    timer = await _get_active_timer(db, workspace_id, timer_id, TimerStatus.RUNNING)
    now = datetime.now(UTC)
    started_at = _ensure_aware(timer.started_at)
    elapsed = (now - started_at).total_seconds()
    timer.actual_seconds = int(elapsed)
    timer.status = TimerStatus.PAUSED
    timer.paused_at = now
    await db.commit()
    await db.refresh(timer)

    await remove_timer_job(timer_id)

    return timer


async def resume_timer(
    db: AsyncSession, workspace_id: str, timer_id: str
) -> TimerSession:
    """Resume a paused timer and schedule a new finish job."""

    timer = await _get_active_timer(db, workspace_id, timer_id, TimerStatus.PAUSED)
    now = datetime.now(UTC)

    elapsed_before_pause = timer.actual_seconds
    remaining = max(0, timer.estimated_seconds - elapsed_before_pause)

    timer.status = TimerStatus.RUNNING
    timer.paused_at = None
    timer.actual_seconds = elapsed_before_pause
    await db.commit()
    await db.refresh(timer)

    if remaining > 0:
        finish_at = now + timedelta(seconds=remaining)
        await schedule_timer_finish(
            timer_id=timer.id,
            workspace_id=workspace_id,
            run_at=finish_at,
            task_id=timer.task_id,
        )

    return timer


async def cancel_timer(
    db: AsyncSession, workspace_id: str, timer_id: str
) -> TimerSession:
    """Cancel a running or paused timer and remove its APS job."""

    timer = await _get_active_timer(
        db, workspace_id, timer_id,
        allowed_statuses=[TimerStatus.RUNNING, TimerStatus.PAUSED],
    )
    now = datetime.now(UTC)

    if timer.status == TimerStatus.RUNNING:
        started_at = _ensure_aware(timer.started_at)
        elapsed = (now - started_at).total_seconds()
        timer.actual_seconds = int(elapsed)

    timer.status = TimerStatus.CANCELLED
    timer.finished_at = now
    await db.commit()
    await db.refresh(timer)

    await remove_timer_job(timer_id)

    return timer


async def complete_timer(
    db: AsyncSession, timer_id: str, workspace_id: str
) -> TimerSession:
    """Mark a timer as completed (called by APScheduler job)."""

    timer = await get_timer_by_id(db, workspace_id, timer_id)
    if timer is None or timer.status != TimerStatus.RUNNING:
        return None

    timer.status = TimerStatus.COMPLETED
    timer.finished_at = datetime.now(UTC)

    started_at = _ensure_aware(timer.started_at)
    finished_at = _ensure_aware(timer.finished_at)
    elapsed = (finished_at - started_at).total_seconds()
    timer.actual_seconds = int(elapsed)

    await db.commit()
    await db.refresh(timer)
    return timer


async def get_timer_by_id(
    db: AsyncSession, workspace_id: str, timer_id: str
) -> TimerSession | None:
    """Return one timer session scoped to workspace."""

    result = await db.execute(
        select(TimerSession).where(
            TimerSession.id == timer_id,
            TimerSession.workspace_id == workspace_id,
        )
    )
    return result.scalar_one_or_none()


async def get_timer_history(
    db: AsyncSession, workspace_id: str, task_id: str
) -> list[TimerSession]:
    """Return all timer sessions for a given task."""

    result = await db.execute(
        select(TimerSession)
        .where(
            TimerSession.workspace_id == workspace_id,
            TimerSession.task_id == task_id,
        )
        .order_by(TimerSession.started_at.desc())
    )
    return list(result.scalars().all())


async def get_running_timers(
    db: AsyncSession, workspace_id: str | None = None
) -> list[TimerSession]:
    """Return all timers currently in running state."""

    query = select(TimerSession).where(
        TimerSession.status == TimerStatus.RUNNING)

    if workspace_id:
        query = query.where(TimerSession.workspace_id == workspace_id)

    query = query.order_by(TimerSession.started_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def _get_active_timer(
    db: AsyncSession,
    workspace_id: str,
    timer_id: str,
    allowed_statuses: TimerStatus | list[TimerStatus] | None = None,
) -> TimerSession:
    """Fetch a timer and verify it belongs to the workspace and has the right status."""

    timer = await get_timer_by_id(db, workspace_id, timer_id)
    if timer is None:
        raise ValueError("Timer session not found")

    if allowed_statuses is not None:
        if isinstance(allowed_statuses, TimerStatus):
            allowed_statuses = [allowed_statuses]
        if timer.status not in allowed_statuses:
            raise ValueError(
                f"Timer is in status '{timer.status.value}', "
                f"expected one of: {[s.value for s in allowed_statuses]}"
            )

    return timer
