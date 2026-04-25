"""update notification timestamps to timezone aware.

Revision ID: 485b8c902cdd
Revises: 2d7a78c32a14
Create Date: 2026-04-25 19:22:09.577555

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '485b8c902cdd'
down_revision: str | Sequence[str] | None = '2d7a78c32a14'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Convert scheduled_time and sent_at columns from TIMESTAMP to TIMESTAMP WITH TIME ZONE
    op.alter_column(
        'notification_recipients',
        'scheduled_time',
        existing_type=sa.DateTime(),
        type_=sa.TIMESTAMP(timezone=True),
        existing_nullable=True,
    )
    op.alter_column(
        'notification_recipients',
        'sent_at',
        existing_type=sa.DateTime(),
        type_=sa.TIMESTAMP(timezone=True),
        existing_nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Revert back to TIMESTAMP WITHOUT TIME ZONE
    op.alter_column(
        'notification_recipients',
        'scheduled_time',
        existing_type=sa.TIMESTAMP(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=True,
    )
    op.alter_column(
        'notification_recipients',
        'sent_at',
        existing_type=sa.TIMESTAMP(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=True,
    )
