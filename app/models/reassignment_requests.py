"""SQLAlchemy model for reassignment requests."""

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import DomainSqlModel


class ReassignmentRequests(DomainSqlModel):
    """A request from one group member to take over another member's assignment."""

    __tablename__ = 'reassignment_requests'

    reminder_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(),
        sa.ForeignKey('reminders.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    # The member who *wants* to take over
    requester_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(),
        sa.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
    )
    # The current assignee who must approve/reject
    current_assignee_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(),
        sa.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    # 'pending' | 'accepted' | 'rejected'
    status: Mapped[str] = mapped_column(sa.String(20), nullable=False, default='pending')
    message: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(sa.TIMESTAMP(timezone=True), nullable=True)
