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

    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    is_completed: Mapped[bool] = mapped_column(default=False)

    updated_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    completed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # Relationships
    owner = relationship('Users', foreign_keys=[owner_id], back_populates='owned_reminders')
    updated_by_user = relationship(
        'Users',
        foreign_keys=[updated_by],
    )
    completed_by_user = relationship(
        'Users',
        foreign_keys=[completed_by],
    )
    notifications = relationship(
        'NotificationRecipients',
        back_populates='reminder',
    )
