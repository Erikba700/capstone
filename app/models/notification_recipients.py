import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.models import DomainSqlModel


class NotificationRecipients(DomainSqlModel):
    """Model for notification recipients."""

    __tablename__ = 'notification_recipients'

    reminder_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey('reminders.id', ondelete='CASCADE'), nullable=True)
    user_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey('users.id', ondelete='CASCADE'))

    message: Mapped[str] = mapped_column(sa.String, nullable=True)
    creator_email: Mapped[str] = mapped_column(sa.String, nullable=True)
    scheduled_time: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), nullable=True)
    sent_at: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), nullable=True)
    is_read_at: Mapped[datetime | None] = mapped_column(sa.TIMESTAMP(timezone=True), nullable=True)
