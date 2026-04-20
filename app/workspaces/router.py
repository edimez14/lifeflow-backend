from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.workspaces.schemas import (
    WorkspaceCreate,
    WorkspaceResponse,
    WorkspaceUpdate,
)
from app.workspaces.service import (
    create_workspace,
    delete_workspace,
    get_workspace_by_id,
    list_workspaces,
    update_workspace,
)


router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("", response_model=list[WorkspaceResponse])
async def read_workspaces(db: AsyncSession = Depends(get_db)) -> list[WorkspaceResponse]:
    """Return all workspaces."""

    return await list_workspaces(db)


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace_view(
    payload: WorkspaceCreate,
    db: AsyncSession = Depends(get_db),
) -> WorkspaceResponse:
    """Create a new workspace."""

    try:
        return await create_workspace(db, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def read_workspace(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> WorkspaceResponse:
    """Return one workspace by id."""

    workspace = await get_workspace_by_id(db, workspace_id)
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return workspace


@router.put("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace_view(
    workspace_id: str,
    payload: WorkspaceUpdate,
    db: AsyncSession = Depends(get_db),
) -> WorkspaceResponse:
    """Update one workspace."""

    workspace = await get_workspace_by_id(db, workspace_id)
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return await update_workspace(db, workspace, payload)


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace_view(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete one workspace."""

    workspace = await get_workspace_by_id(db, workspace_id)
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    await delete_workspace(db, workspace)
