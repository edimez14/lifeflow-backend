from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base


class EventCategory(str, Enum):
    """Categories para organizar eventos."""
    IMPORTANTE = "importante"
    URGENTE = "urgente"
    ESPECIAL = "especial"
    REPETITIVO = "repetitivo"
    SOLO_UNA_VEZ = "solo_una_vez"


# Map de colores por categoria
CATEGORY_COLORS = {
    EventCategory.IMPORTANTE: "#FF9800",     # naranja
    EventCategory.URGENTE: "#F44336",        # rojo
    EventCategory.ESPECIAL: "#9C27B0",       # morado
    EventCategory.REPETITIVO: "#2196F3",     # azul
    EventCategory.SOLO_UNA_VEZ: "#4CAF50",   # verde
}


class Calendar(Base):
    """Calendar entity linked to one workspace."""

    __tablename__ = "calendars"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    color: Mapped[str] = mapped_column(String(30), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Event(Base):
    """Calendar event entity with optional recurrence settings."""

    __tablename__ = "events"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    calendar_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("calendars.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False)
    end_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False)
    recurrence_rule: Mapped[str | None] = mapped_column(Text, nullable=True)
    color: Mapped[str | None] = mapped_column(String(30), nullable=True)
    category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    is_exception: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False)
    parent_event_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("events.id", ondelete="SET NULL"),
        nullable=True,
    )


class MonthlyGoal(Base):
    """Monthly goal entity linked to one workspace and month."""

    __tablename__ = "monthly_goals"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    goal_text: Mapped[str] = mapped_column(Text, nullable=False)
    action_plan: Mapped[str] = mapped_column(Text, nullable=False)
