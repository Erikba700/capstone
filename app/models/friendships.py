import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.entities.friendship import FriendshipStatus
from app.models.base import DomainSqlModel


class Friendships(DomainSqlModel):
    """SQLAlchemy model for friendships."""

    __tablename__ = 'friendships'
    __table_args__ = (sa.UniqueConstraint('requester_id', 'addressee_id', name='uq_friendship_pair'),)

    requester_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    addressee_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    status: Mapped[FriendshipStatus] = mapped_column(
        sa.Enum(
            FriendshipStatus,
            name='friendshipstatus',
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=FriendshipStatus.PENDING,
        server_default=FriendshipStatus.PENDING.value,
    )
    accepted_at: Mapped[sa.DateTime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )
