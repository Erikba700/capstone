import uuid

from pydantic import AwareDatetime

from app.schemas.base_schemas import BaseSchema


class RemindersCreateRequestSchema(BaseSchema):
    """Schema for creating a new reminder."""

    title: str
    description: str | None = None
    owner_id: uuid.UUID
    is_completed: bool = False


class RemindersCreateResponseSchema(BaseSchema):
    """Schema for response after creating a new reminder."""

    id: uuid.UUID
    title: str
    description: str | None = None
    owner_id: uuid.UUID
    is_completed: bool = False
    created_at: AwareDatetime
    updated_at: AwareDatetime
