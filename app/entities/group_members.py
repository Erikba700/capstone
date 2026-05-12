import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Self

from app.entities.domain_entity import DomainEntity

if TYPE_CHECKING:
    from app.entities.user import UserEntity


class MemberRoles(enum.StrEnum):
    """Roles of group member.

    owner - the user who created the group and has full control over it
    admin - users with elevated permissions, can manage members and edit group details
    member - regular users with access to group content and be able to assign reminders
    but limited management capabilities
    """

    OWNER = 'owner'
    ADMIN = 'admin'
    MEMBER = 'member'


class GroupMembersEntity(DomainEntity):
    """GroupMembers domain entity."""

    user_id: uuid.UUID
    group_id: uuid.UUID
    role: MemberRoles
    joined_at: datetime

    @classmethod
    def create_new(
        cls,
        user_id: uuid.UUID,
        group_id: uuid.UUID,
        role: MemberRoles = MemberRoles.MEMBER,
        joined_at: datetime | None = None,
    ) -> Self:
        """Construct new group member."""
        id_ = cls.generate_id()
        now = cls.generate_current_timestamp()
        return cls(
            id=id_,
            created_at=now,
            updated_at=now,
            user_id=user_id,
            group_id=group_id,
            role=role,
            joined_at=joined_at or now,
        )

    def update(self, payload: dict[str, Any], user: UserEntity) -> Self:
        """Update current group member with new data from payload."""
        now = self.generate_current_timestamp()

        model = self.model_copy(update=payload, deep=True)

        model.updated_at = now

        return model
