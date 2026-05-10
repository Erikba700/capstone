import uuid

from pydantic import AwareDatetime

from app.schemas.base_schemas import BaseSchema


class UserSignUpResponseSchema(BaseSchema):
    """User return schema for sing up."""

    id: uuid.UUID
    name: str
    email: str | None = None
    hashed_password: str | None = None
    created_at: AwareDatetime
    updated_at: AwareDatetime


class UserSignUpRequestSchema(BaseSchema):
    """User schema for sing up request."""

    name: str
    email: str
    password: str
    timezone: str = 'UTC'  # Default to UTC if not provided


class UserLoginResponseSchema(BaseSchema):
    """User response schema for token fields."""

    access_token: str
    refresh_token: str


class TokenPayloadSchema(BaseSchema):
    """Token payload schema for token validation."""

    sub: str
    exp: int


class UserUpdateRequestSchema(BaseSchema):
    """Schema for updating user profile."""

    name: str | None = None
    timezone: str | None = None
    current_password: str | None = None
    new_password: str | None = None


class UserProfileResponseSchema(BaseSchema):
    """Schema for user profile response."""

    id: uuid.UUID
    name: str
    email: str
    timezone: str
    created_at: AwareDatetime
    updated_at: AwareDatetime
