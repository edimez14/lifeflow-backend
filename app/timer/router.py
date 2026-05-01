from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.timer.schemas import (
    TimerHistoryItem,
    TimerResponse,
    TimerStartRequest,
)
from app.timer.service import (
    cancel_timer,
    get_timer_by_id,
    get_timer_history,
    pause_timer,
    resume_timer,
    start_timer,
)
from app.websocket_manager import ConnectionManager, get_connection_manager


router = APIRouter(tags=["timer"])


@router.post(
    "/timers/start",
    response_model=TimerResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_timer_view(
    payload: TimerStartRequest,
    db: AsyncSession = Depends(get_db),
    manager: ConnectionManager = Depends(get_connection_manager),
) -> TimerResponse:
    """Start a new timer session for the user's workspace."""

    if not payload.workspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="workspace_id is required",
        )

    timer = await start_timer(db, payload.workspace_id, payload)

    await manager.broadcast(payload.workspace_id, {
        "type": "timer.started",
        "data": TimerResponse.model_validate(timer).model_dump(),
    })

    return TimerResponse.model_validate(timer)


@router.post(
    "/timers/{timer_id}/pause",
    response_model=TimerResponse,
)
async def pause_timer_view(
    timer_id: str,
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    manager: ConnectionManager = Depends(get_connection_manager),
) -> TimerResponse:
    """Pause a running timer."""

    try:
        timer = await pause_timer(db, workspace_id, timer_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    await manager.broadcast(workspace_id, {
        "type": "timer.paused",
        "data": TimerResponse.model_validate(timer).model_dump(),
    })

    return TimerResponse.model_validate(timer)


@router.post(
    "/timers/{timer_id}/resume",
    response_model=TimerResponse,
)
async def resume_timer_view(
    timer_id: str,
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    manager: ConnectionManager = Depends(get_connection_manager),
) -> TimerResponse:
    """Resume a paused timer."""

    try:
        timer = await resume_timer(db, workspace_id, timer_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    await manager.broadcast(workspace_id, {
        "type": "timer.resumed",
        "data": TimerResponse.model_validate(timer).model_dump(),
    })

    return TimerResponse.model_validate(timer)


@router.post(
    "/timers/{timer_id}/cancel",
    response_model=TimerResponse,
)
async def cancel_timer_view(
    timer_id: str,
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    manager: ConnectionManager = Depends(get_connection_manager),
) -> TimerResponse:
    """Cancel a running or paused timer."""

    try:
        timer = await cancel_timer(db, workspace_id, timer_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    await manager.broadcast(workspace_id, {
        "type": "timer.cancelled",
        "data": TimerResponse.model_validate(timer).model_dump(),
    })

    return TimerResponse.model_validate(timer)


@router.get(
    "/timers/{timer_id}",
    response_model=TimerResponse,
)
async def get_timer_view(
    timer_id: str,
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> TimerResponse:
    """Get details of one timer session."""

    timer = await get_timer_by_id(db, workspace_id, timer_id)
    if timer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timer session not found",
        )

    return TimerResponse.model_validate(timer)


@router.get(
    "/timers/history/{task_id}",
    response_model=list[TimerHistoryItem],
)
async def get_timer_history_view(
    task_id: str,
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[TimerHistoryItem]:
    """Return timer session history for a specific task."""

    sessions = await get_timer_history(db, workspace_id, task_id)
    return [TimerHistoryItem.model_validate(s) for s in sessions]
