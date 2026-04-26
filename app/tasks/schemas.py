from __future__ import annotations

from datetime import date, time

from pydantic import BaseModel, ConfigDict

from app.tasks.types import TaskPriority, TaskStatus


# ---------- TaskList ----------

class TaskListBase(BaseModel):
    """Shared task list fields."""

    name: str
    color: str


class TaskListCreate(TaskListBase):
    """Data used to create a task list."""


class TaskListUpdate(BaseModel):
    """Data used to update a task list."""

    name: str | None = None
    color: str | None = None


class TaskListResponse(TaskListBase):
    """Task list data returned by API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str


# ---------- Task ----------

class TaskBase(BaseModel):
    """Shared task fields."""

    title: str
    description: str | None = None
    due_date: date | None = None
    due_time: time | None = None
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    order: int = 0
    category_id: str | None = None


class TaskCreate(TaskBase):
    """Data used to create a task."""

    task_list_id: str
    project_id: str | None = None


class TaskUpdate(BaseModel):
    """Data used to update a task."""

    title: str | None = None
    description: str | None = None
    due_date: date | None = None
    due_time: time | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    order: int | None = None
    category_id: str | None = None
    project_id: str | None = None


class TaskResponse(TaskBase):
    """Task data returned by API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    task_list_id: str
    project_id: str | None


class TaskReorderItem(BaseModel):
    """Single item for reorder payload."""

    id: str
    order: int


class TaskReorderRequest(BaseModel):
    """Payload to reorder tasks inside a list."""

    items: list[TaskReorderItem]


class TaskCompletionResponse(BaseModel):
    """Completion percentage for a task based on subtasks."""

    task_id: str
    total_subtasks: int
    completed_subtasks: int
    percentage: float


# ---------- SubTask ----------

class SubTaskBase(BaseModel):
    """Shared subtask fields."""

    title: str
    completed: bool = False
    order: int = 0


class SubTaskCreate(SubTaskBase):
    """Data used to create a subtask."""


class SubTaskUpdate(BaseModel):
    """Data used to update a subtask."""

    title: str | None = None
    completed: bool | None = None
    order: int | None = None


class SubTaskResponse(SubTaskBase):
    """Subtask data returned by API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: str
