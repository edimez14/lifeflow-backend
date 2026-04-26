from __future__ import annotations

from datetime import date

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.tasks.models import SubTask, Task, TaskCategory, TaskList
from app.tasks.schemas import (
    SubTaskCreate,
    SubTaskUpdate,
    TaskCreate,
    TaskUpdate,
    TaskListCreate,
    TaskListUpdate,
    TaskReorderRequest,
)
from app.tasks.types import TaskPriority, TaskStatus


# ---------- TaskList ----------

async def list_task_lists(db: AsyncSession, workspace_id: str) -> list[TaskList]:
    """Return all task lists for a workspace."""

    result = await db.execute(
        select(TaskList)
        .where(TaskList.workspace_id == workspace_id)
        .order_by(TaskList.name.asc())
    )
    return list(result.scalars().all())


async def get_task_list_by_id(
    db: AsyncSession, workspace_id: str, task_list_id: str
) -> TaskList | None:
    """Return one workspace task list by id."""

    result = await db.execute(
        select(TaskList).where(
            TaskList.workspace_id == workspace_id,
            TaskList.id == task_list_id,
        )
    )
    return result.scalar_one_or_none()


async def create_task_list(
    db: AsyncSession, workspace_id: str, payload: TaskListCreate
) -> TaskList:
    """Create a new task list inside a workspace."""

    task_list = TaskList(workspace_id=workspace_id, **payload.model_dump())
    db.add(task_list)
    await db.commit()
    await db.refresh(task_list)
    return task_list


async def update_task_list(
    db: AsyncSession, task_list: TaskList, payload: TaskListUpdate
) -> TaskList:
    """Update an existing task list."""

    update_data = payload.model_dump(exclude_unset=True)
    for field_name, value in update_data.items():
        setattr(task_list, field_name, value)
    await db.commit()
    await db.refresh(task_list)
    return task_list


async def delete_task_list(db: AsyncSession, task_list: TaskList) -> None:
    """Delete a task list and all related tasks."""

    await db.delete(task_list)
    await db.commit()


# ---------- Task ----------

async def list_tasks(
    db: AsyncSession,
    workspace_id: str,
    list_id: str | None = None,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    due_date: date | None = None,
) -> list[Task]:
    """Return tasks for a workspace, optionally filtered."""

    query = (
        select(Task)
        .join(TaskList, TaskList.id == Task.task_list_id)
        .where(TaskList.workspace_id == workspace_id)
    )
    if list_id:
        query = query.where(Task.task_list_id == list_id)
    if status:
        query = query.where(Task.status == status)
    if priority:
        query = query.where(Task.priority == priority)
    if due_date:
        query = query.where(Task.due_date == due_date)

    query = query.order_by(Task.order.asc(), Task.title.asc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_task_by_id(
    db: AsyncSession, workspace_id: str, task_id: str
) -> Task | None:
    """Return one workspace task by id."""

    result = await db.execute(
        select(Task)
        .join(TaskList, TaskList.id == Task.task_list_id)
        .where(
            TaskList.workspace_id == workspace_id,
            Task.id == task_id,
        )
    )
    return result.scalar_one_or_none()


async def create_task(
    db: AsyncSession, workspace_id: str, payload: TaskCreate
) -> Task:
    """Create a new task inside a workspace task list."""

    task_list = await db.scalar(
        select(TaskList).where(
            TaskList.id == payload.task_list_id,
            TaskList.workspace_id == workspace_id,
        )
    )
    if task_list is None:
        raise ValueError("Task list not found")

    task_data = payload.model_dump()
    task = Task(**task_data)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def update_task(
    db: AsyncSession, task: Task, payload: TaskUpdate
) -> Task:
    """Update an existing task."""

    update_data = payload.model_dump(exclude_unset=True)
    for field_name, value in update_data.items():
        setattr(task, field_name, value)
    await db.commit()
    await db.refresh(task)
    return task


async def delete_task(db: AsyncSession, task: Task) -> None:
    """Delete a task and its subtasks."""

    await db.delete(task)
    await db.commit()


async def reorder_tasks(
    db: AsyncSession,
    workspace_id: str,
    task_list_id: str,
    payload: TaskReorderRequest,
) -> list[Task]:
    """Update the order of multiple tasks in a single transaction."""

    # Validate that all tasks belong to the given list and workspace
    task_ids = [item.id for item in payload.items]
    stmt = (
        select(Task)
        .join(TaskList, TaskList.id == Task.task_list_id)
        .where(
            TaskList.workspace_id == workspace_id,
            Task.task_list_id == task_list_id,
            Task.id.in_(task_ids),
        )
    )
    result = await db.execute(stmt)
    existing_tasks = result.scalars().all()

    if len(existing_tasks) != len(task_ids):
        raise ValueError("One or more tasks not found in the specified list")

    # Build a mapping of id -> new order
    order_map = {item.id: item.order for item in payload.items}

    for task in existing_tasks:
        task.order = order_map[task.id]

    await db.commit()

    # Re-fetch in the new order
    new_result = await db.execute(
        select(Task)
        .where(Task.task_list_id == task_list_id)
        .order_by(Task.order.asc())
    )
    return list(new_result.scalars().all())


async def get_task_completion(
    db: AsyncSession, workspace_id: str, task_id: str
) -> dict:
    """Return completion stats for a task based on its subtasks."""

    # Verify task belongs to workspace
    task = await get_task_by_id(db, workspace_id, task_id)
    if task is None:
        raise ValueError("Task not found")

    subtask_result = await db.execute(
        select(SubTask).where(SubTask.task_id == task_id)
    )
    subtasks = subtask_result.scalars().all()

    total = len(subtasks)
    completed = sum(1 for st in subtasks if st.completed)
    percentage = (completed / total * 100) if total > 0 else 0.0

    return {
        "task_id": task_id,
        "total_subtasks": total,
        "completed_subtasks": completed,
        "percentage": percentage,
    }


# ---------- SubTask ----------

async def list_subtasks(
    db: AsyncSession, workspace_id: str, task_id: str
) -> list[SubTask]:
    """Return subtasks for a given task."""

    result = await db.execute(
        select(SubTask)
        .join(Task, Task.id == SubTask.task_id)
        .join(TaskList, TaskList.id == Task.task_list_id)
        .where(
            TaskList.workspace_id == workspace_id,
            SubTask.task_id == task_id,
        )
        .order_by(SubTask.order.asc(), SubTask.title.asc())
    )
    return list(result.scalars().all())


async def get_subtask_by_id(
    db: AsyncSession, workspace_id: str, subtask_id: str
) -> SubTask | None:
    """Return one subtask by id, scoped to workspace."""

    result = await db.execute(
        select(SubTask)
        .join(Task, Task.id == SubTask.task_id)
        .join(TaskList, TaskList.id == Task.task_list_id)
        .where(
            TaskList.workspace_id == workspace_id,
            SubTask.id == subtask_id,
        )
    )
    return result.scalar_one_or_none()


async def create_subtask(
    db: AsyncSession, workspace_id: str, task_id: str, payload: SubTaskCreate
) -> SubTask:
    """Create a new subtask for an existing task."""

    task = await get_task_by_id(db, workspace_id, task_id)
    if task is None:
        raise ValueError("Task not found")

    subtask = SubTask(task_id=task_id, **payload.model_dump())
    db.add(subtask)
    await db.commit()
    await db.refresh(subtask)
    return subtask


async def update_subtask(
    db: AsyncSession, subtask: SubTask, payload: SubTaskUpdate
) -> SubTask:
    """Update an existing subtask."""

    update_data = payload.model_dump(exclude_unset=True)
    for field_name, value in update_data.items():
        setattr(subtask, field_name, value)
    await db.commit()
    await db.refresh(subtask)
    return subtask


async def delete_subtask(db: AsyncSession, subtask: SubTask) -> None:
    """Delete a subtask."""

    await db.delete(subtask)
    await db.commit()
