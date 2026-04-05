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


class UserLoginResponseSchema(BaseSchema):
    """User response schema for token fields."""

    access_token: str
    refresh_token: str


class TokenPayloadSchema(BaseSchema):
    """Token payload schema for token validation."""

    sub: str
    exp: int
