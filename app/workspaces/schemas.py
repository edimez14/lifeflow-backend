from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.workspaces.types import WorkspaceType


class WorkspaceBase(BaseModel):
    """Shared workspace fields used by create and update schemas."""

    name: str
    workspace_type: WorkspaceType
    color: str
    icon: str


class WorkspaceCreate(WorkspaceBase):
    """Data needed to create a workspace."""

    password: Optional[str] = None


class WorkspaceUpdate(BaseModel):
    """Data needed to update a workspace."""

    name: Optional[str] = None
    workspace_type: Optional[WorkspaceType] = None
    password: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None


class WorkspaceResponse(BaseModel):
    """Workspace data returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    workspace_type: WorkspaceType
    color: str
    icon: str
    created_at: datetime
    updated_at: datetime
