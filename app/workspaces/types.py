from __future__ import annotations

import enum


class WorkspaceType(str, enum.Enum):
    """Workspace visibility types."""

    PUBLIC = "public"
    PRIVATE = "private"
