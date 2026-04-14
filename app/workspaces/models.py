from __future__ import annotations

import uuid

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, TimestampMixin
from app.workspaces.types import WorkspaceType


class Workspace(Base, TimestampMixin):
    """Workspace entity used to isolate data per context."""

    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    workspace_type: Mapped[WorkspaceType] = mapped_column(
        Enum(
            WorkspaceType,
            name="workspace_type",
            values_callable=lambda enum_values: [
                item.value for item in enum_values],
            native_enum=False,
        ),
        nullable=False,
        default=WorkspaceType.PUBLIC,
    )
    password_hash: Mapped[str | None] = mapped_column(
        String(255), nullable=True)
    color: Mapped[str] = mapped_column(String(30), nullable=False)
    icon: Mapped[str] = mapped_column(String(80), nullable=False)
