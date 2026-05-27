"""add is_completed to monthly_goals

Revision ID: f0ecadae5b92
Revises: 6f1e4a3b2c8d
Create Date: 2026-05-17 21:58:43.572080

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f0ecadae5b92'
down_revision: Union[str, Sequence[str], None] = '6f1e4a3b2c8d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add is_completed column to monthly_goals table."""
    op.add_column('monthly_goals', sa.Column('is_completed',
                  sa.Boolean(), nullable=False, server_default=sa.text('0')))


def downgrade() -> None:
    """Remove is_completed column from monthly_goals table."""
    op.drop_column('monthly_goals', 'is_completed')
