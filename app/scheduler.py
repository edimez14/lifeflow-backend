from __future__ import annotations

from datetime import UTC, datetime, timedelta

from apscheduler.jobstores.base import ConflictingIdError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.websocket_manager import get_connection_manager

TICK_JOB_ID = "timer_tick_every_second"

_scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler:
    """Return the global APScheduler singleton (lazy init)."""

    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    return _scheduler


# ── Finish jobs (one per timer) ──────────────────────────

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

    await _ensure_tick_job_running()


async def remove_timer_job(timer_id: str) -> None:
    """Remove a previously scheduled timer finish job."""

    scheduler = get_scheduler()
    job_id = _job_id(timer_id)
    existing = scheduler.get_job(job_id)
    if existing is not None:
        scheduler.remove_job(job_id)

    await _pause_tick_if_no_timers()


async def _finish_timer_job(timer_id: str, workspace_id: str, task_id: str | None) -> None:
    """Execute when the timer reaches its deadline."""

    from app.database import AsyncSessionLocal
    from app.timer.service import complete_timer

    async with AsyncSessionLocal() as db:
        timer = await complete_timer(db, timer_id, workspace_id)
        if timer is not None:
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

    await _pause_tick_if_no_timers()


# ── Tick job (broadcast every second) ────────────────────

async def _ensure_tick_job_running() -> None:
    """Start the per-second tick job if it is not already running."""

    scheduler = get_scheduler()
    existing = scheduler.get_job(TICK_JOB_ID)
    if existing is not None:
        return

    scheduler.add_job(
        _tick_job,
        trigger=IntervalTrigger(seconds=1),
        id=TICK_JOB_ID,
        replace_existing=True,
        misfire_grace_time=2,
    )


async def _pause_tick_if_no_timers() -> None:
    """Remove the tick job if there are no running timers left."""

    from app.database import AsyncSessionLocal
    from app.timer.service import get_running_timers

    async with AsyncSessionLocal() as db:
        running = await get_running_timers(db)

    if running:
        return

    scheduler = get_scheduler()
    existing = scheduler.get_job(TICK_JOB_ID)
    if existing is not None:
        scheduler.remove_job(TICK_JOB_ID)


async def _tick_job() -> None:
    """Broadcast remaining seconds for every running timer across all workspaces."""

    from app.database import AsyncSessionLocal
    from app.timer.service import get_running_timers

    async with AsyncSessionLocal() as db:
        timers = await get_running_timers(db)

    if not timers:
        return

    now = datetime.now(UTC)
    manager = get_connection_manager()

    workspace_groups: dict[str, list[dict]] = {}
    for timer in timers:
        elapsed = (now - timer.started_at).total_seconds()
        remaining = max(0, timer.estimated_seconds - int(elapsed))

        workspace_groups.setdefault(timer.workspace_id, []).append({
            "timer_id": timer.id,
            "task_id": timer.task_id,
            "remaining_seconds": remaining,
            "elapsed_seconds": int(elapsed),
            "estimated_seconds": timer.estimated_seconds,
        })

    for workspace_id, ticks in workspace_groups.items():
        await manager.broadcast(
            workspace_id,
            {
                "type": "timer.tick",
                "data": ticks,
            },
        )


# ── Helpers ──────────────────────────────────────────────

def _job_id(timer_id: str) -> str:
    """Return the APScheduler job id for a given timer session."""

    return f"timer_finish_{timer_id}"
