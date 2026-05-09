import uuid
from typing import Any, Self

from app.entities.domain_entity import DomainEntity


class UserEntity(DomainEntity):
    """User domain entity."""

    id: uuid.UUID
    name: str
    email: str
    hashed_password: str
    timezone: str

    @classmethod
    def create_new(
        cls,
        name: str,
        email: str,
        hashed_password: str,
        timezone: str = 'UTC',
    ) -> Self:
        """Construct new user."""
        id_ = cls.generate_id()
        now = cls.generate_current_timestamp()
        return cls(
            id=id_,
            created_at=now,
            updated_at=now,
            name=name,
            email=email,
            hashed_password=hashed_password,
            timezone=timezone,
        )

    def update(
        self,
        payload: dict[str, Any],
    ) -> Self:
        """Update current user with new data from payload."""
        now = self.generate_current_timestamp()

        model = self.model_copy(update=payload, deep=True)

        model.updated_at = now

        return model
