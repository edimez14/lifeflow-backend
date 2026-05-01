"""add timer_sessions table

Revision ID: 6f1e4a3b2c8d
Revises: b0d76dfedea2
Create Date: 2026-04-26 18:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6f1e4a3b2c8d"
down_revision: str | None = "b0d76dfedea2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "timer_sessions",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column(
            "task_id",
            sa.String(36),
            sa.ForeignKey("tasks.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "workspace_id",
            sa.String(36),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("estimated_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("actual_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "status",
            sa.Enum(
                "running", "paused", "completed", "cancelled",
                name="timer_status",
                native_enum=False,
            ),
            nullable=False,
            server_default="running",
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paused_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_timer_sessions_workspace_id",
        "timer_sessions",
        ["workspace_id"],
    )
    op.create_index(
        "ix_timer_sessions_task_id",
        "timer_sessions",
        ["task_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_timer_sessions_task_id", table_name="timer_sessions")
    op.drop_index("ix_timer_sessions_workspace_id", table_name="timer_sessions")
    op.drop_table("timer_sessions")
    op.execute("DROP TYPE IF EXISTS timer_status")
