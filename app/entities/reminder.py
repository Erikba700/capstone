import uuid
from typing import TYPE_CHECKING, Any, Self

from app.entities.domain_entity import DomainEntity

if TYPE_CHECKING:
    from app.entities.user import UserEntity


class ReminderEntity(DomainEntity):
    """Reminder domain entity."""

    title: str
    description: str | None
    owner_id: uuid.UUID
    is_completed: bool
    updated_by: uuid.UUID | None = None
    completed_by: uuid.UUID | None = None

    @classmethod
    def create_new(
        cls,
        title: str,
        description: str | None,
        owner_id: uuid.UUID,
        *,
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
            owner_id=owner_id,
            is_completed=is_completed,
        )

    def update(self, payload: dict[str, Any], user: UserEntity) -> Self:
        """Update current reminder with new data from payload."""
        now = self.generate_current_timestamp()

        model = self.model_copy(update=payload, deep=True)

        model.updated_at = now
        model.updated_by = user.id
        model.completed_by = user.id if payload.get('is_completed') else None

        return model
