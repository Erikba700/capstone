import uuid
from typing import Self

from pydantic import AwareDatetime, model_validator

from app.schemas.base_schemas import BaseSchema


class RemindersCreateRequestSchema(BaseSchema):
    """Schema for creating a new reminder."""

    title: str
    description: str | None = None
    is_completed: bool = False
    scheduled_time: AwareDatetime | None = None
    user_id: uuid.UUID | None = None

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
    is_completed: bool = False
    created_at: AwareDatetime
    updated_at: AwareDatetime
    scheduled_time: AwareDatetime | None = None  # When notification is scheduled
    notified_immediately: bool = False  # True if notification was sent immediately


class RemindersListResponseSchema(BaseSchema):
    """Schema for response when listing reminders."""

    reminders: list[RemindersResponseSchema]


class RemindersFiltersSchema(BaseSchema):
    """Schema for filtering reminders."""

    is_completed: bool | None = None


class RemindersUpdateRequestSchema(BaseSchema):
    """Schema for updating a reminder."""

    title: str | None = None
    description: str | None = None
    is_completed: bool | None = None
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
