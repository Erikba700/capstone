"""Re-add group_id to reminders (dropped by mistake in previous migration).

Revision ID: 8de1b9ab0c5f
Revises: 3dec003a745b
Create Date: 2026-05-13 02:44:40.636943

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = '8de1b9ab0c5f'
down_revision: str | Sequence[str] | None = '3dec003a745b'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
