# reminder.py
import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import DomainSqlModel


class Reminders(DomainSqlModel):
    """Sqlalchemy model for reminders."""

    __tablename__ = 'reminders'

    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True
    )

    is_completed: Mapped[bool] = mapped_column(default=False)

    # Relationships
    owner = relationship('Users', back_populates='owned_reminders')
    notifications = relationship(
        'NotificationRecipients',
        back_populates='reminder',
    )
