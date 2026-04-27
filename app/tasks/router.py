from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.tasks.schemas import (
    SubTaskCreate,
    SubTaskResponse,
    SubTaskUpdate,
    TaskCategoryCreate,
    TaskCategoryResponse,
    TaskCategoryUpdate,
    TaskCompletionResponse,
    TaskCreate,
    TaskListCreate,
    TaskListResponse,
    TaskListUpdate,
    TaskReorderRequest,
    TaskResponse,
    TaskUpdate,
)
from app.tasks.service import (
    create_subtask,
    create_task,
    create_task_category,
    create_task_list,
    delete_subtask,
    delete_task,
    delete_task_category,
    delete_task_list,
    get_subtask_by_id,
    get_task_by_id,
    get_task_category_by_id,
    get_task_completion,
    get_task_list_by_id,
    list_subtasks,
    list_task_categories,
    list_task_lists,
    list_tasks,
    reorder_tasks,
    update_subtask,
    update_task,
    update_task_category,
    update_task_list,
)
from app.tasks.types import TaskPriority, TaskStatus


router = APIRouter(tags=["tasks"])


# ---------- TaskLists ----------

@router.get(
    "/workspaces/{workspace_id}/task-lists",
    response_model=list[TaskListResponse],
)
async def read_task_lists(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[TaskListResponse]:
    """List task lists for one workspace."""

    lists = await list_task_lists(db, workspace_id)
    return [TaskListResponse.model_validate(tl) for tl in lists]


@router.post(
    "/workspaces/{workspace_id}/task-lists",
    response_model=TaskListResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task_list_view(
    workspace_id: str,
    payload: TaskListCreate,
    db: AsyncSession = Depends(get_db),
) -> TaskListResponse:
    """Create a new task list in a workspace."""

    task_list = await create_task_list(db, workspace_id, payload)
    return TaskListResponse.model_validate(task_list)


@router.put(
    "/workspaces/{workspace_id}/task-lists/{task_list_id}",
    response_model=TaskListResponse,
)
async def update_task_list_view(
    workspace_id: str,
    task_list_id: str,
    payload: TaskListUpdate,
    db: AsyncSession = Depends(get_db),
) -> TaskListResponse:
    """Update one workspace task list."""

    task_list = await get_task_list_by_id(db, workspace_id, task_list_id)
    if task_list is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task list not found",
        )
    updated = await update_task_list(db, task_list, payload)
    return TaskListResponse.model_validate(updated)


@router.delete(
    "/workspaces/{workspace_id}/task-lists/{task_list_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_task_list_view(
    workspace_id: str,
    task_list_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete one workspace task list."""

    task_list = await get_task_list_by_id(db, workspace_id, task_list_id)
    if task_list is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task list not found",
        )
    await delete_task_list(db, task_list)


# ---------- Tasks ----------

@router.get(
    "/workspaces/{workspace_id}/tasks",
    response_model=list[TaskResponse],
)
async def read_tasks(
    workspace_id: str,
    list_id: str | None = Query(None),
    status_filter: TaskStatus | None = Query(None, alias="status"),
    priority: TaskPriority | None = Query(None),
    due_date: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> list[TaskResponse]:
    """List workspace tasks with optional filters."""

    tasks = await list_tasks(
        db,
        workspace_id,
        list_id=list_id,
        status=status_filter,
        priority=priority,
        due_date=due_date,
    )
    return [TaskResponse.model_validate(task) for task in tasks]


@router.post(
    "/workspaces/{workspace_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task_view(
    workspace_id: str,
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """Create one task in a workspace."""

    try:
        task = await create_task(db, workspace_id, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return TaskResponse.model_validate(task)


@router.put(
    "/workspaces/{workspace_id}/tasks/{task_id}",
    response_model=TaskResponse,
)
async def update_task_view(
    workspace_id: str,
    task_id: str,
    payload: TaskUpdate,
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """Update one workspace task."""

    task = await get_task_by_id(db, workspace_id, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    updated = await update_task(db, task, payload)
    return TaskResponse.model_validate(updated)


@router.delete(
    "/workspaces/{workspace_id}/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_task_view(
    workspace_id: str,
    task_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete one workspace task."""

    task = await get_task_by_id(db, workspace_id, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    await delete_task(db, task)


@router.patch(
    "/workspaces/{workspace_id}/task-lists/{task_list_id}/tasks/reorder",
    response_model=list[TaskResponse],
)
async def reorder_tasks_view(
    workspace_id: str,
    task_list_id: str,
    payload: TaskReorderRequest,
    db: AsyncSession = Depends(get_db),
) -> list[TaskResponse]:
    """Reorder tasks inside a list."""

    try:
        tasks = await reorder_tasks(db, workspace_id, task_list_id, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return [TaskResponse.model_validate(task) for task in tasks]


@router.get(
    "/workspaces/{workspace_id}/tasks/{task_id}/completion",
    response_model=TaskCompletionResponse,
)
async def get_task_completion_view(
    workspace_id: str,
    task_id: str,
    db: AsyncSession = Depends(get_db),
) -> TaskCompletionResponse:
    """Return completion percentage for a task based on subtasks."""

    try:
        stats = await get_task_completion(db, workspace_id, task_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return TaskCompletionResponse(**stats)


# ---------- SubTasks ----------

@router.get(
    "/workspaces/{workspace_id}/tasks/{task_id}/subtasks",
    response_model=list[SubTaskResponse],
)
async def read_subtasks(
    workspace_id: str,
    task_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[SubTaskResponse]:
    """List subtasks of a given task."""

    subtasks = await list_subtasks(db, workspace_id, task_id)
    return [SubTaskResponse.model_validate(st) for st in subtasks]


@router.post(
    "/workspaces/{workspace_id}/tasks/{task_id}/subtasks",
    response_model=SubTaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_subtask_view(
    workspace_id: str,
    task_id: str,
    payload: SubTaskCreate,
    db: AsyncSession = Depends(get_db),
) -> SubTaskResponse:
    """Create a new subtask for a task."""

    try:
        subtask = await create_subtask(db, workspace_id, task_id, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return SubTaskResponse.model_validate(subtask)


@router.put(
    "/workspaces/{workspace_id}/tasks/{task_id}/subtasks/{subtask_id}",
    response_model=SubTaskResponse,
)
async def update_subtask_view(
    workspace_id: str,
    task_id: str,
    subtask_id: str,
    payload: SubTaskUpdate,
    db: AsyncSession = Depends(get_db),
) -> SubTaskResponse:
    """Update one subtask."""

    subtask = await get_subtask_by_id(db, workspace_id, subtask_id)
    if subtask is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subtask not found",
        )
    updated = await update_subtask(db, subtask, payload)
    return SubTaskResponse.model_validate(updated)


@router.delete(
    "/workspaces/{workspace_id}/tasks/{task_id}/subtasks/{subtask_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_subtask_view(
    workspace_id: str,
    task_id: str,
    subtask_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete one subtask."""

    subtask = await get_subtask_by_id(db, workspace_id, subtask_id)
    if subtask is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subtask not found",
        )
    await delete_subtask(db, subtask)


# ---------- TaskCategories ----------

@router.get(
    "/workspaces/{workspace_id}/task-categories",
    response_model=list[TaskCategoryResponse],
)
async def read_task_categories(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[TaskCategoryResponse]:
    """List task categories for one workspace."""

    categories = await list_task_categories(db, workspace_id)
    return [TaskCategoryResponse.model_validate(cat) for cat in categories]


@router.post(
    "/workspaces/{workspace_id}/task-categories",
    response_model=TaskCategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task_category_view(
    workspace_id: str,
    payload: TaskCategoryCreate,
    db: AsyncSession = Depends(get_db),
) -> TaskCategoryResponse:
    """Create a new task category in a workspace."""

    category = await create_task_category(db, workspace_id, payload)
    return TaskCategoryResponse.model_validate(category)


@router.put(
    "/workspaces/{workspace_id}/task-categories/{category_id}",
    response_model=TaskCategoryResponse,
)
async def update_task_category_view(
    workspace_id: str,
    category_id: str,
    payload: TaskCategoryUpdate,
    db: AsyncSession = Depends(get_db),
) -> TaskCategoryResponse:
    """Update one workspace task category."""

    category = await get_task_category_by_id(db, workspace_id, category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    updated = await update_task_category(db, category, payload)
    return TaskCategoryResponse.model_validate(updated)


@router.delete(
    "/workspaces/{workspace_id}/task-categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_task_category_view(
    workspace_id: str,
    category_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete one workspace task category. Tasks using it will lose the category."""

    category = await get_task_category_by_id(db, workspace_id, category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    await delete_task_category(db, category)
