from __future__ import annotations

from datetime import datetime, timedelta

from apscheduler.jobstores.base import ConflictingIdError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from app.websocket_manager import get_connection_manager

_scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler:
    """Return the global APScheduler singleton (lazy init)."""

    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    return _scheduler


async def schedule_timer_finish(
    timer_id: str,
    workspace_id: str,
    run_at: datetime,
    task_id: str | None = None,
) -> None:
    """Schedule a one-time APS job that fires when the timer should end."""

    scheduler = get_scheduler()
    job_id = _job_id(timer_id)

    try:
        scheduler.add_job(
            _finish_timer_job,
            trigger=DateTrigger(run_date=run_at),
            id=job_id,
            args=[timer_id, workspace_id, task_id],
            replace_existing=False,
            misfire_grace_time=60,
        )
    except ConflictingIdError:
        pass


async def remove_timer_job(timer_id: str) -> None:
    """Remove a previously scheduled timer finish job."""

    scheduler = get_scheduler()
    job_id = _job_id(timer_id)
    existing = scheduler.get_job(job_id)
    if existing is not None:
        scheduler.remove_job(job_id)


async def _finish_timer_job(timer_id: str, workspace_id: str, task_id: str | None) -> None:
    """Execute when the timer reaches its deadline."""

    from app.database import AsyncSessionLocal
    from app.timer.service import complete_timer

    async with AsyncSessionLocal() as db:
        timer = await complete_timer(db, timer_id, workspace_id)
        manager = get_connection_manager()
        await manager.broadcast(
            workspace_id,
            {
                "type": "timer.finished",
                "data": {
                    "timer_id": timer_id,
                    "task_id": task_id,
                    "workspace_id": workspace_id,
                    "actual_seconds": timer.actual_seconds,
                },
            },
        )


def _job_id(timer_id: str) -> str:
    """Return the APScheduler job id for a given timer session."""

    return f"timer_finish_{timer_id}"
