"""Merge heads.

Revision ID: 2605713ce543
Revises: 8de1b9ab0c5f, c1d2e3f4a5b6
Create Date: 2026-05-21 14:49:11.165060

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = '2605713ce543'
down_revision: str | Sequence[str] | None = ('8de1b9ab0c5f', 'c1d2e3f4a5b6')
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
