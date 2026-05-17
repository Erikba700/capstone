"""Add is_read_at to notification_recipients, acknowledged_at to reminder_assignees.

Revision ID: c1d2e3f4a5b6
Revises: a1b2c3d4e5f6
Create Date: 2026-05-16 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'c1d2e3f4a5b6'
down_revision: str | None = 'a1b2c3d4e5f6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Migrate is_read → is_read_at and add acknowledged_at."""
    # 1. Add is_read_at column (nullable)
    op.add_column(
        'notification_recipients',
        sa.Column('is_read_at', sa.TIMESTAMP(timezone=True), nullable=True),
    )
    # 3. Drop the old boolean column
    op.drop_column('notification_recipients', 'is_read')

    # 4. Add acknowledged_at to reminder_assignees
    op.add_column(
        'reminder_assignees',
        sa.Column('acknowledged_at', sa.TIMESTAMP(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Revert: restore is_read boolean, drop is_read_at and acknowledged_at."""
    op.add_column(
        'notification_recipients',
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
    )
    op.drop_column('notification_recipients', 'is_read_at')
    op.drop_column('reminder_assignees', 'acknowledged_at')
