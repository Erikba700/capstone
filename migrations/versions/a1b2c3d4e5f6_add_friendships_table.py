"""Add friendships table.

Revision ID: a1b2c3d4e5f6
Revises: b3ad26fd8e05
Create Date: 2026-05-13 04:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'a1b2c3d4e5f6'
down_revision: str | Sequence[str] | None = 'b3ad26fd8e05'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE TYPE friendshipstatus AS ENUM ('pending', 'accepted', 'rejected', 'blocked')")
    op.create_table(
        'friendships',
        sa.Column('requester_id', sa.UUID(), nullable=False),
        sa.Column('addressee_id', sa.UUID(), nullable=False),
        sa.Column(
            'status',
            sa.Enum('pending', 'accepted', 'rejected', 'blocked', name='friendshipstatus'),
            nullable=False,
            server_default='pending',
        ),
        sa.Column('accepted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['addressee_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['requester_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('requester_id', 'addressee_id', name='uq_friendship_pair'),
    )
    op.create_index('ix_friendships_requester_id', 'friendships', ['requester_id'], unique=False)
    op.create_index('ix_friendships_addressee_id', 'friendships', ['addressee_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_friendships_addressee_id', table_name='friendships')
    op.drop_index('ix_friendships_requester_id', table_name='friendships')
    op.drop_table('friendships')
    op.execute('DROP TYPE friendshipstatus')
