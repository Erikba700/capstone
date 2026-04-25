"""add creator_email to notifications.

Revision ID: f82bb466a060
Revises: 485b8c902cdd
Create Date: 2026-04-25 20:23:50.922192

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f82bb466a060'
down_revision: str | Sequence[str] | None = '485b8c902cdd'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add creator_email column to notification_recipients table
    op.add_column(
        'notification_recipients',
        sa.Column('creator_email', sa.String(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove creator_email column from notification_recipients table
    op.drop_column('notification_recipients', 'creator_email')
