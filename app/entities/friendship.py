import enum
import uuid
from datetime import datetime
from typing import Self

from app.entities.domain_entity import DomainEntity


class FriendshipStatus(enum.StrEnum):
    """Possible statuses for a friendship."""

    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    BLOCKED = 'blocked'


class FriendshipEntity(DomainEntity):
    """Friendship domain entity."""

    requester_id: uuid.UUID
    addressee_id: uuid.UUID
    status: FriendshipStatus = FriendshipStatus.PENDING
    accepted_at: datetime | None = None

    @classmethod
    def create_new(
        cls,
        requester_id: uuid.UUID,
        addressee_id: uuid.UUID,
    ) -> Self:
        """Construct new pending friendship request."""
        id_ = cls.generate_id()
        now = cls.generate_current_timestamp()
        return cls(
            id=id_,
            created_at=now,
            updated_at=now,
            requester_id=requester_id,
            addressee_id=addressee_id,
            status=FriendshipStatus.PENDING,
            accepted_at=None,
        )

    def accept(self) -> Self:
        """Accept the friendship request."""
        now = self.generate_current_timestamp()
        return self.model_copy(
            update={
                'status': FriendshipStatus.ACCEPTED,
                'accepted_at': now,
                'updated_at': now,
            }
        )

    def reject(self) -> Self:
        """Reject the friendship request."""
        now = self.generate_current_timestamp()
        return self.model_copy(update={'status': FriendshipStatus.REJECTED, 'updated_at': now})

    def block(self) -> Self:
        """Block the other user."""
        now = self.generate_current_timestamp()
        return self.model_copy(update={'status': FriendshipStatus.BLOCKED, 'updated_at': now})
