# reminder.py
import uuid

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.entities.reminder import ReminderStatus
from app.models import DomainSqlModel


class Reminders(DomainSqlModel):
    """Sqlalchemy model for reminders."""

    __tablename__ = 'reminders'

    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    status: Mapped[ReminderStatus] = mapped_column(
        Enum(ReminderStatus, name='reminderstatus', values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=ReminderStatus.PENDING,
        server_default=ReminderStatus.PENDING.value,
    )

    updated_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    completed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    group_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey('groups.id', ondelete='SET NULL'), nullable=True, index=True
    )
