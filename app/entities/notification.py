import uuid
from datetime import datetime
from typing import Any, Self

from pydantic import AwareDatetime

from app.entities.domain_entity import DomainEntity


class NotificationEntity(DomainEntity):
    """Notification domain entity."""

    user_id: uuid.UUID
    reminder_id: uuid.UUID
    message: str | None
    creator_email: str | None
    scheduled_time: AwareDatetime | None
    sent_at: datetime | None
    is_read: bool

    @classmethod
    def create_new(
        cls,
        user_id: uuid.UUID,
        reminder_id: uuid.UUID,
        message: str | None = None,
        creator_email: str | None = None,
        scheduled_time: AwareDatetime | None = None,
        sent_at: datetime | None = None,
        *,
        is_read: bool = False,
    ) -> Self:
        """Construct new notification."""
        id_ = cls.generate_id()
        now = cls.generate_current_timestamp()
        return cls(
            id=id_,
            user_id=user_id,
            reminder_id=reminder_id,
            message=message,
            creator_email=creator_email,
            scheduled_time=scheduled_time,
            sent_at=sent_at,
            is_read=is_read,
            created_at=now,
            updated_at=now,
        )

    def update(
        self,
        payload: dict[str, Any],
    ) -> Self:
        """Update current notification with new data from payload."""
        now = self.generate_current_timestamp()

        model = self.model_copy(update=payload, deep=True)

        model.updated_at = now

        return model
