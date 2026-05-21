"""Domain entity for reassignment requests."""

import uuid
from datetime import datetime

from app.entities.domain_entity import DomainEntity


class ReassignmentRequestEntity(DomainEntity):
    """A request by a group member to take over another member's reminder assignment."""

    reminder_id: uuid.UUID
    requester_id: uuid.UUID
    current_assignee_id: uuid.UUID
    status: str = 'pending'
    message: str | None = None
    resolved_at: datetime | None = None

    @classmethod
    def create_new(
        cls,
        reminder_id: uuid.UUID,
        requester_id: uuid.UUID,
        current_assignee_id: uuid.UUID,
        message: str | None = None,
    ) -> 'ReassignmentRequestEntity':
        """Factory method."""
        now = cls.generate_current_timestamp()
        return cls(
            id=cls.generate_id(),
            reminder_id=reminder_id,
            requester_id=requester_id,
            current_assignee_id=current_assignee_id,
            status='pending',
            message=message,
            resolved_at=None,
            created_at=now,
            updated_at=now,
        )
