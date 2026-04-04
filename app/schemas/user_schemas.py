import uuid

from pydantic import Field, AwareDatetime

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

class UserResponseSchema(BaseSchema):
    """User response schema for getting user."""

    id: uuid.UUID
    name: str
    sid: str | None


class UserSearchResponseSchema(BaseSchema):
    """User schema for user search."""

    id: uuid.UUID
    name: str


class UserSearchSchema(BaseSchema):
    """Schema for user search parameters."""

    substring: str = Field(..., description='Name substring to search')
    size: int = Field(20, ge=1, le=1_000, description='Max number of results')
