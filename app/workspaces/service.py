from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.workspaces.models import Workspace
from app.workspaces.schemas import WorkspaceCreate, WorkspaceUpdate
from app.workspaces.types import WorkspaceType


async def list_workspaces(db: AsyncSession) -> list[Workspace]:
    """Return all workspaces ordered by creation date."""

    result = await db.execute(select(Workspace).order_by(Workspace.created_at.desc()))
    return list(result.scalars().all())


async def get_workspace_by_id(db: AsyncSession, workspace_id: str) -> Workspace | None:
    """Return one workspace by id or None when it does not exist."""

    result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    return result.scalar_one_or_none()


async def create_workspace(db: AsyncSession, payload: WorkspaceCreate) -> Workspace:
    """Create one workspace and hash the password when it is private."""

    workspace_data = payload.model_dump()
    password = workspace_data.pop("password", None)

    password_hash: str | None = None
    if payload.workspace_type == WorkspaceType.PRIVATE:
        if not password:
            raise ValueError("Password is required for private workspaces")
        password_hash = hash_password(password)

    workspace = Workspace(
        **workspace_data,
        password_hash=password_hash,
    )

    db.add(workspace)
    await db.commit()
    await db.refresh(workspace)
    return workspace


async def update_workspace(
    db: AsyncSession,
    workspace: Workspace,
    payload: WorkspaceUpdate,
) -> Workspace:
    """Update one workspace with optional password handling."""

    update_data = payload.model_dump(exclude_unset=True)
    password = update_data.pop("password", None)

    next_workspace_type = update_data.get(
        "workspace_type", workspace.workspace_type)

    for field_name, value in update_data.items():
        setattr(workspace, field_name, value)

    if next_workspace_type == WorkspaceType.PRIVATE:
        if password:
            workspace.password_hash = hash_password(password)
    else:
        workspace.password_hash = None

    await db.commit()
    await db.refresh(workspace)
    return workspace


async def delete_workspace(db: AsyncSession, workspace: Workspace) -> None:
    """Delete one workspace."""

    await db.delete(workspace)
    await db.commit()
