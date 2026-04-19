import uuid

from pydantic import AwareDatetime

from app.schemas.base_schemas import BaseSchema


class RemindersCreateRequestSchema(BaseSchema):
    """Schema for creating a new reminder."""

    title: str
    description: str | None = None
    is_completed: bool = False


class RemindersResponseSchema(BaseSchema):
    """Schema for response after creating a new reminder."""

    id: uuid.UUID
    title: str
    description: str | None = None
    owner_id: uuid.UUID
    is_completed: bool = False
    created_at: AwareDatetime
    updated_at: AwareDatetime


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
