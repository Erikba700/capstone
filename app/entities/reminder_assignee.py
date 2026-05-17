import uuid
from datetime import datetime
from typing import Self

from app.entities.domain_entity import DomainEntity


class ReminderAssigneeEntity(DomainEntity):
    """Reminder assignee domain entity (many-to-many: reminders <-> users)."""

    reminder_id: uuid.UUID
    user_id: uuid.UUID
    assigned_by: uuid.UUID
    assigned_at: datetime
    acknowledged_at: datetime | None = None
    completed_at: datetime | None = None

    @classmethod
    def create_new(
        cls,
        reminder_id: uuid.UUID,
        user_id: uuid.UUID,
        assigned_by: uuid.UUID,
    ) -> Self:
        """Construct new reminder assignee."""
        id_ = cls.generate_id()
        now = cls.generate_current_timestamp()
        return cls(
            id=id_,
            created_at=now,
            updated_at=now,
            reminder_id=reminder_id,
            user_id=user_id,
            assigned_by=assigned_by,
            assigned_at=now,
            acknowledged_at=None,
            completed_at=None,
        )

    def acknowledge(self) -> 'ReminderAssigneeEntity':
        """Mark this assignment as acknowledged (seen) by setting acknowledged_at."""
        now = self.generate_current_timestamp()
        return self.model_copy(update={'acknowledged_at': now, 'updated_at': now})

    def complete(self) -> 'ReminderAssigneeEntity':
        """Mark this assignment as completed by setting completed_at."""
        now = self.generate_current_timestamp()
        return self.model_copy(update={'completed_at': now, 'updated_at': now})
