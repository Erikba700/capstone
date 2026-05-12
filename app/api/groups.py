import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.dependencies import get_current_user, get_repo, get_shared_tx_repo
from app.entities import UserEntity
from app.exceptions import BadRequestError
from app.repos import RepoFactory
from app.schemas.group_schemas import (
    GroupCreateRequestSchema,
    GroupMemberAddRequestSchema,
    GroupMemberResponseSchema,
    GroupMemberUpdateRequestSchema,
    GroupResponseSchema,
    GroupUpdateRequestSchema,
)
from app.schemas.reminder_schemas import RemindersListResponseSchema
from app.services.group_service import GroupService
from app.services.reminder_service import ReminderService

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


@router.get('/groups/{group_id}/members', response_model=list[GroupMemberResponseSchema])
async def list_members(
    group_id: uuid.UUID,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_repo)],
) -> object:
    """List members of a group. Caller must be a member."""
    service = GroupService(repos=repos)
    await service.require_membership(group_id=group_id, user_id=user.id)
    return await service.list_members(group_id=group_id)


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
) -> object:
    """Add a user to a group by email. Requires admin or owner."""
    service = GroupService(repos=repos)
    await service.require_admin(group_id=group_id, user_id=user.id)

    # Resolve email → user
    target_user = await repos.user_pgsql_repo.find_by_username(email=schema.email)
    if target_user is None:
        msg = f'User with email {schema.email} not found'
        raise BadRequestError(msg)

    return await service.add_member(
        group_id=group_id,
        user_id=target_user.id,
        role=schema.role,
    )


@router.patch('/groups/{group_id}/members/{target_user_id}', response_model=GroupMemberResponseSchema)
async def update_member_role(
    group_id: uuid.UUID,
    target_user_id: uuid.UUID,
    schema: GroupMemberUpdateRequestSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> object:
    """Change a member's role. Requires admin or owner."""
    service = GroupService(repos=repos)
    actor_membership = await service.require_admin(group_id=group_id, user_id=user.id)
    return await service.update_member_role(
        group_id=group_id,
        target_user_id=target_user_id,
        new_role=schema.role,
        actor_role=actor_membership.role,
    )


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
