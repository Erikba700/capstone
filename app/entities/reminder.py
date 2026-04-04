import uuid
from typing import Self, Any

from app.entities import DomainEntity


class ReminderEntity(DomainEntity):
    """Reminder domain entity."""

    title: str
    description: str | None
    owner_id: str
    is_completed: bool

    @classmethod
    def create_new(
            cls,
            title: str,
            description: str | None,
            owner_id: uuid.UUID,
            is_completed: bool = False,
    ) -> Self:
        """Construct new reminder."""
        id_ = cls.generate_id()
        now = cls.generate_current_timestamp()
        return cls(
            id=id_,
            created_at=now,
            updated_at=now,
            title=title,
            description=description,
            owner_id=str(owner_id),
            is_completed=is_completed,
        )

    def update(self, payload: dict[str, Any]) -> Self:
        """Update current reminder with new data from payload."""
        now = self.generate_current_timestamp()

        model = self.model_copy(update=payload, deep=True)

        model.updated_at = now

        return model