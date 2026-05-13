import uuid
from datetime import datetime

from pydantic import AwareDatetime

from app.entities.friendship import FriendshipStatus
from app.schemas.base_schemas import BaseSchema


class FriendshipCreateRequestSchema(BaseSchema):
    """Schema for sending a friend request."""

    addressee_id: uuid.UUID


class FriendshipUpdateRequestSchema(BaseSchema):
    """Schema for accepting or rejecting a friend request."""

    status: FriendshipStatus


class FriendshipResponseSchema(BaseSchema):
    """Schema for friendship response."""

    id: uuid.UUID
    requester_id: uuid.UUID
    addressee_id: uuid.UUID
    status: FriendshipStatus
    accepted_at: datetime | None = None
    created_at: AwareDatetime
    updated_at: AwareDatetime


class FriendUserSchema(BaseSchema):
    """Minimal user info returned alongside a friendship."""

    id: uuid.UUID
    name: str
    email: str


class FriendshipWithUserResponseSchema(BaseSchema):
    """Friendship response enriched with the other user's info."""

    id: uuid.UUID
    requester_id: uuid.UUID
    addressee_id: uuid.UUID
    status: FriendshipStatus
    accepted_at: datetime | None = None
    created_at: AwareDatetime
    updated_at: AwareDatetime
    other_user: FriendUserSchema


class UserSearchItemSchema(BaseSchema):
    """Single user in search results."""

    id: uuid.UUID
    name: str
    email: str


class UserSearchResponseSchema(BaseSchema):
    """Paginated user search results."""

    users: list[UserSearchItemSchema]
    total: int
    page: int
    page_size: int
