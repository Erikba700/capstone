import uuid

from pydantic import AwareDatetime

from app.entities.group_members import MemberRoles
from app.schemas.base_schemas import BaseSchema


class GroupCreateRequestSchema(BaseSchema):
    """Schema for creating a group."""

    name: str
    description: str | None = None


class GroupUpdateRequestSchema(BaseSchema):
    """Schema for updating a group."""

    name: str | None = None
    description: str | None = None


class GroupResponseSchema(BaseSchema):
    """Schema for group response."""

    id: uuid.UUID
    name: str
    description: str | None = None
    owner_id: uuid.UUID
    created_at: AwareDatetime
    updated_at: AwareDatetime


class GroupMemberResponseSchema(BaseSchema):
    """Schema for group member response."""

    id: uuid.UUID
    user_id: uuid.UUID
    user_name: str
    user_email: str
    group_id: uuid.UUID
    role: MemberRoles
    joined_at: AwareDatetime
    created_at: AwareDatetime
    updated_at: AwareDatetime


class GroupMemberAddRequestSchema(BaseSchema):
    """Schema for adding a member to a group by email."""

    email: str
    role: MemberRoles = MemberRoles.MEMBER


class GroupMemberUpdateRequestSchema(BaseSchema):
    """Schema for updating a group member role."""

    role: MemberRoles


class AssigneeResponseSchema(BaseSchema):
    """Schema for reminder assignee response."""

    id: uuid.UUID
    reminder_id: uuid.UUID
    user_id: uuid.UUID
    assigned_by: uuid.UUID
    assigned_at: AwareDatetime
    completed_at: AwareDatetime | None = None
    created_at: AwareDatetime
    updated_at: AwareDatetime


class AddAssigneeRequestSchema(BaseSchema):
    """Schema for adding an assignee to a reminder."""

    user_id: uuid.UUID


class CompleteAssignmentRequestSchema(BaseSchema):
    """Schema for completing a reminder assignment."""

    completed: bool = True
