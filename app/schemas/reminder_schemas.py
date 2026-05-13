import uuid
from typing import Self

from pydantic import AwareDatetime, model_validator

from app.entities.reminder import ReminderStatus
from app.schemas.base_schemas import BaseSchema


class AssigneeInfoSchema(BaseSchema):
    """Minimal assignee info embedded in reminder responses."""

    id: uuid.UUID  # assignment id
    user_id: uuid.UUID
    user_name: str | None = None
    user_email: str | None = None
    assigned_by: uuid.UUID
    assigned_by_name: str | None = None
    assigned_at: AwareDatetime
    completed_at: AwareDatetime | None = None


class RemindersCreateRequestSchema(BaseSchema):
    """Schema for creating a new reminder."""

    title: str
    description: str | None = None
    status: ReminderStatus = ReminderStatus.PENDING
    scheduled_time: AwareDatetime | None = None
    user_id: uuid.UUID | None = None
    group_id: uuid.UUID | None = None
    assignee_ids: list[uuid.UUID] | None = None
    notify_assignees: bool = False
    assignee_scheduled_time: AwareDatetime | None = None

    @model_validator(mode='after')
    def validate_scheduled_time_requires_user_id(self) -> Self:
        """Validate that if scheduled_time is provided, user_id must also be provided."""
        if self.scheduled_time is not None and self.user_id is None:
            msg = 'user_id must be provided when scheduled_time is set'
            raise ValueError(msg)
        return self


class RemindersResponseSchema(BaseSchema):
    """Schema for response after creating a new reminder."""

    id: uuid.UUID
    title: str
    description: str | None = None
    owner_id: uuid.UUID
    status: ReminderStatus = ReminderStatus.PENDING
    group_id: uuid.UUID | None = None
    updated_by: uuid.UUID | None = None
    updated_by_name: str | None = None
    created_at: AwareDatetime
    updated_at: AwareDatetime
    scheduled_time: AwareDatetime | None = None
    notified_immediately: bool = False
    assignees: list[uuid.UUID] = []  # noqa: RUF012
    assignee_details: list[AssigneeInfoSchema] = []  # noqa: RUF012


class RemindersListResponseSchema(BaseSchema):
    """Schema for response when listing reminders."""

    reminders: list[RemindersResponseSchema]


class RemindersFiltersSchema(BaseSchema):
    """Schema for filtering reminders."""

    status: ReminderStatus | None = None
    include_assigned: bool = True


class RemindersUpdateRequestSchema(BaseSchema):
    """Schema for updating a reminder."""

    title: str | None = None
    description: str | None = None
    status: ReminderStatus | None = None
    owner_id: uuid.UUID | None = None
    scheduled_time: AwareDatetime | None = None
    user_id: uuid.UUID | None = None

    @model_validator(mode='after')
    def validate_scheduled_time_requires_user_id(self) -> Self:
        """Validate that if scheduled_time is provided, user_id must also be provided."""
        if self.scheduled_time is not None and self.user_id is None:
            msg = 'user_id must be provided when scheduled_time is set'
            raise ValueError(msg)
        return self
