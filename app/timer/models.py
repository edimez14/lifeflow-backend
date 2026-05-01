from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base
from app.timer.types import TimerStatus


class TimerSession(Base):
    """Records a timer session linked to an optional task."""

    __tablename__ = "timer_sessions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    task_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
    )
    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    estimated_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    actual_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    status: Mapped[TimerStatus] = mapped_column(
        Enum(
            TimerStatus,
            name="timer_status",
            values_callable=lambda enum_values: [
                item.value for item in enum_values
            ],
            native_enum=False,
        ),
        nullable=False,
        default=TimerStatus.RUNNING,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    paused_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
