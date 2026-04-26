from __future__ import annotations

import uuid
from datetime import date, time

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base
from app.tasks.types import TaskPriority, TaskStatus


class TaskList(Base):
    """Task list entity linked to one workspace."""

    __tablename__ = "task_lists"

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


class TaskCategory(Base):
    """Custom category created by user for tasks."""

    __tablename__ = "task_categories"

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


class Task(Base):
    """Task entity with optional schedule, category and project link."""

    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    task_list_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("task_lists.id", ondelete="CASCADE"),
        nullable=False,
    )
    project_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(
            TaskPriority,
            name="task_priority",
            values_callable=lambda enum_values: [
                item.value for item in enum_values],
            native_enum=False,
        ),
        nullable=False,
        default=TaskPriority.NORMAL,
    )
    status: Mapped[TaskStatus] = mapped_column(
        Enum(
            TaskStatus,
            name="task_status",
            values_callable=lambda enum_values: [
                item.value for item in enum_values],
            native_enum=False,
        ),
        nullable=False,
        default=TaskStatus.PENDING,
    )
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    category_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("task_categories.id", ondelete="SET NULL"),
        nullable=True,
    )


class SubTask(Base):
    """Subtask entity linked to one parent task."""

    __tablename__ = "subtasks"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    task_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    completed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
