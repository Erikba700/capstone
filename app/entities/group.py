import uuid
from typing import TYPE_CHECKING, Any, Self

from app.entities.domain_entity import DomainEntity

if TYPE_CHECKING:
    from app.entities.user import UserEntity


class GroupEntity(DomainEntity):
    """GroupMembers domain entity."""

    name: str
    description: str | None
    owner_id: uuid.UUID

    @classmethod
    def create_new(
        cls,
        name: str,
        owner_id: uuid.UUID,
        description: str | None = None,
    ) -> Self:
        """Construct new group member."""
        id_ = cls.generate_id()
        now = cls.generate_current_timestamp()
        return cls(
            id=id_,
            created_at=now,
            updated_at=now,
            name=name,
            description=description,
            owner_id=owner_id,
        )

    def update(self, payload: dict[str, Any], user: UserEntity) -> Self:
        """Update current group member with new data from payload."""
        now = self.generate_current_timestamp()

        model = self.model_copy(update=payload, deep=True)

        model.updated_at = now

        return model
