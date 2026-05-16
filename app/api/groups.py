import re
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.dependencies import get_current_user, get_repo, get_shared_tx_repo
from app.entities import UserEntity
from app.exceptions import BadRequestError
from app.repos import RepoFactory
from app.schemas.friendship_schemas import UserSearchItemSchema, UserSearchResponseSchema
from app.schemas.group_schemas import (
    GroupCreateRequestSchema,
    GroupInviteRequestSchema,
    GroupInviteResponseSchema,
    GroupMemberAddRequestSchema,
    GroupMemberResponseSchema,
    GroupMemberUpdateRequestSchema,
    GroupResponseSchema,
    GroupUpdateRequestSchema,
)
from app.schemas.reminder_schemas import RemindersListResponseSchema
from app.services.group_service import GroupService
from app.services.reminder_service import ReminderService

_EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

router = APIRouter(tags=['Groups'])


@router.post('/groups', response_model=GroupResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_group(
    schema: GroupCreateRequestSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> object:
    """Create a new group. Creator is automatically added as owner."""
    service = GroupService(repos=repos)
    return await service.create_group(schema=schema, owner_id=user.id)


@router.get('/groups', response_model=list[GroupResponseSchema])
async def list_groups(
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_repo)],
) -> object:
    """List all groups the current user belongs to."""
    service = GroupService(repos=repos)
    return await service.list_user_groups(user_id=user.id)


@router.get('/groups/{group_id}', response_model=GroupResponseSchema)
async def get_group(
    group_id: uuid.UUID,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_repo)],
) -> object:
    """Get a group by id. Caller must be a member."""
    service = GroupService(repos=repos)
    await service.require_membership(group_id=group_id, user_id=user.id)
    return await service.fetch_group(group_id=group_id)


@router.patch('/groups/{group_id}', response_model=GroupResponseSchema)
async def update_group(
    group_id: uuid.UUID,
    schema: GroupUpdateRequestSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> object:
    """Update group name/description. Requires admin or owner."""
    service = GroupService(repos=repos)
    await service.require_admin(group_id=group_id, user_id=user.id)
    return await service.update_group(group_id=group_id, schema=schema)


@router.delete('/groups/{group_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: uuid.UUID,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> None:
    """Delete a group. Requires owner."""
    service = GroupService(repos=repos)
    await service.require_owner(group_id=group_id, user_id=user.id)
    await service.delete_group(group_id=group_id)


# ── Group reminders ───────────────────────────────────────────────────────────


@router.get('/groups/{group_id}/reminders', response_model=RemindersListResponseSchema)
async def list_group_reminders(
    group_id: uuid.UUID,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_repo)],
) -> dict:
    """List all reminders in a group. Caller must be a member."""
    group_service = GroupService(repos=repos)
    await group_service.require_membership(group_id=group_id, user_id=user.id)

    reminder_service = ReminderService(repos=repos)
    reminders = await reminder_service.list_group_reminders(group_id=group_id)
    enriched = await reminder_service.enrich_reminders_with_notification_info(reminders)
    return {'reminders': enriched}


# ── Member management ─────────────────────────────────────────────────────────


@router.get(
    '/groups/{group_id}/members/search',
    response_model=UserSearchResponseSchema,
    summary='Search users to add to a group (ilike, excludes existing members)',
)
async def search_users_for_group(
    group_id: uuid.UUID,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_repo)],
    search: Annotated[str, Query(min_length=1)] = '',
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> dict:
    """Search users by name/email (ilike). Excludes current user and existing members."""
    service = GroupService(repos=repos)
    await service.require_membership(group_id=group_id, user_id=user.id)

    results = await repos.user_pgsql_repo.search(
        search=search,
        exclude_id=user.id,
        page=page,
        page_size=page_size,
    )

    # Exclude users already in the group
    existing_members = await repos.group_member_pgsql_repo.list_by_group_id(group_id=group_id)
    existing_ids = {m.user_id for m in existing_members}
    filtered = [u for u in results if u.id not in existing_ids]

    return {
        'users': [UserSearchItemSchema(id=u.id, name=u.name, email=u.email) for u in filtered],
        'total': len(filtered),
        'page': page,
        'page_size': page_size,
    }


@router.get('/groups/{group_id}/members', response_model=list[GroupMemberResponseSchema])
async def list_members(
    group_id: uuid.UUID,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_repo)],
) -> list[dict]:
    """List members of a group. Caller must be a member."""
    service = GroupService(repos=repos)
    await service.require_membership(group_id=group_id, user_id=user.id)
    members = await service.list_members(group_id=group_id)
    return await service.enrich_members(members)


@router.post(
    '/groups/{group_id}/members',
    response_model=GroupMemberResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def add_member(
    group_id: uuid.UUID,
    schema: GroupMemberAddRequestSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> dict:
    """Add a user to a group by email. Requires admin or owner."""
    service = GroupService(repos=repos)
    await service.require_admin(group_id=group_id, user_id=user.id)

    # Resolve email → user
    target_user = await repos.user_pgsql_repo.find_by_username(email=schema.email)
    if target_user is None:
        msg = f'User with email {schema.email} not found'
        raise BadRequestError(msg)

    member = await service.add_member(
        group_id=group_id,
        user_id=target_user.id,
        role=schema.role,
    )
    return await service.enrich_member(member)


@router.post(
    '/groups/{group_id}/members/invite',
    response_model=GroupInviteResponseSchema,
    status_code=status.HTTP_200_OK,
    summary='Send an email invitation to a non-registered user',
)
async def invite_member_by_email(
    group_id: uuid.UUID,
    schema: GroupInviteRequestSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> dict:
    """Send an invitation email to a person who is not yet registered.

    Requires admin or owner.  Raises 400 if the email is already registered
    (use the regular add-member endpoint instead) or if the email is invalid.
    """
    if not _EMAIL_RE.match(schema.email):
        msg = 'Invalid email address'
        raise BadRequestError(msg)

    service = GroupService(repos=repos)
    await service.require_admin(group_id=group_id, user_id=user.id)

    # Reject if the user already exists — caller should use add_member instead
    existing = await repos.user_pgsql_repo.find_by_username(email=schema.email)
    if existing is not None:
        msg = f'User with email {schema.email} is already registered. Use the Add Member form instead.'
        raise BadRequestError(msg)

    group = await service.fetch_group(group_id=group_id)
    inviter = await repos.user_pgsql_repo.find_by_id(user.id)
    inviter_name = inviter.name if inviter else 'A member'
    inviter_email = inviter.email if inviter else ''

    service.send_group_invitation(
        group_name=group.name,
        inviter_name=inviter_name,
        inviter_email=inviter_email,
        recipient_email=schema.email,
    )

    return {
        'invited_email': schema.email,
        'message': f'Invitation sent to {schema.email}',
    }


@router.patch('/groups/{group_id}/members/{target_user_id}', response_model=GroupMemberResponseSchema)
async def update_member_role(
    group_id: uuid.UUID,
    target_user_id: uuid.UUID,
    schema: GroupMemberUpdateRequestSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> dict:
    """Change a member's role. Requires admin or owner."""
    service = GroupService(repos=repos)
    actor_membership = await service.require_admin(group_id=group_id, user_id=user.id)
    member = await service.update_member_role(
        group_id=group_id,
        target_user_id=target_user_id,
        new_role=schema.role,
        actor_role=actor_membership.role,
    )
    return await service.enrich_member(member)


@router.delete('/groups/{group_id}/members/{target_user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    group_id: uuid.UUID,
    target_user_id: uuid.UUID,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> None:
    """Remove a member from a group. Requires admin or owner."""
    service = GroupService(repos=repos)
    actor_membership = await service.require_admin(group_id=group_id, user_id=user.id)
    await service.remove_member(
        group_id=group_id,
        target_user_id=target_user_id,
        actor_role=actor_membership.role,
    )
