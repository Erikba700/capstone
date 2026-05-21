"""Group reminder collaboration endpoints.

Jira-style collaborative task management for group reminders:
  POST /reminders/{id}/assign           — admin/owner assign a member
  POST /reminders/{id}/assign-to-me    — any group member self-assigns
  POST /reminders/{id}/notify          — notify current assignees
  POST /reminders/{id}/notify-all      — admin/owner notify all members
  PATCH /reminders/{id}/group-update   — member/admin update with role checks
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.dependencies import get_current_user, get_shared_tx_repo
from app.entities import UserEntity
from app.entities.group_members import MemberRoles
from app.exceptions import AuthorizationError, NotFoundError
from app.repos import RepoFactory
from app.schemas.reminder_schemas import (
    GroupAssignRequestSchema,
    GroupNotifyRequestSchema,
    GroupReminderUpdateRequestSchema,
    NotifyCountResponseSchema,
    RemindersResponseSchema,
)
from app.services.group_reminder_service import GroupReminderService
from app.services.reminder_service import ReminderService

router = APIRouter(tags=['Group Reminders'])


async def _get_reminder_or_404(reminder_id: uuid.UUID, repos: RepoFactory):  # type: ignore[return]  # noqa: ANN202
    """Fetch reminder or raise NotFoundError."""
    reminder = await repos.reminder_pgsql_repo.find_by_id(reminder_id=reminder_id)
    if reminder is None:
        msg = 'Reminder not found'
        raise NotFoundError(msg)
    return reminder


@router.post(
    '/reminders/{reminder_id}/assign',
    response_model=RemindersResponseSchema,
    summary='Assign a group member to a reminder (admin/owner only)',
)
async def assign_group_member(
    reminder_id: uuid.UUID,
    schema: GroupAssignRequestSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> dict:
    """Admin/owner assigns any group member to a group reminder.

    Optionally notify the assignee and/or the previous assignee.
    """
    reminder = await _get_reminder_or_404(reminder_id, repos)
    group_service = GroupReminderService(repos=repos)

    group_id = await group_service.ensure_group_reminder(reminder)
    membership = await group_service.ensure_group_member(group_id=group_id, user_id=user.id)
    if membership.role not in (MemberRoles.ADMIN, MemberRoles.OWNER):
        msg = 'Only admins and owners can assign group reminders to others'
        raise AuthorizationError(msg)

    await group_service.assign_user_to_reminder(
        reminder=reminder,
        assignee_id=schema.user_id,
        assigned_by=user.id,
        notify=schema.notify,
        notify_previous=schema.notify_previous,
        scheduled_time=schema.scheduled_time,
    )

    service = ReminderService(repos=repos)
    refreshed = await repos.reminder_pgsql_repo.find_by_id(reminder_id=reminder_id)
    return await service.enrich_reminder_with_notification_info(refreshed)  # type: ignore[arg-type]


@router.post(
    '/reminders/{reminder_id}/assign-to-me',
    response_model=RemindersResponseSchema,
    summary='Self-assign a group reminder (any member)',
)
async def assign_to_me(
    reminder_id: uuid.UUID,
    schema: GroupNotifyRequestSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> dict:
    """Any group member can take ownership of a group reminder.

    Optionally notify the previous assignee.
    """
    reminder = await _get_reminder_or_404(reminder_id, repos)
    group_service = GroupReminderService(repos=repos)

    group_id = await group_service.ensure_group_reminder(reminder)
    membership = await group_service.ensure_group_member(group_id=group_id, user_id=user.id)
    if membership.role not in (MemberRoles.ADMIN, MemberRoles.OWNER):
        msg = 'Only admins and owners can self-assign group reminders'
        raise AuthorizationError(msg)

    await group_service.self_assign(
        reminder=reminder,
        user=user,
        notify_previous=schema.notify_previous,
        scheduled_time=schema.scheduled_time,
    )

    service = ReminderService(repos=repos)
    refreshed = await repos.reminder_pgsql_repo.find_by_id(reminder_id=reminder_id)
    return await service.enrich_reminder_with_notification_info(refreshed)  # type: ignore[arg-type]


@router.post(
    '/reminders/{reminder_id}/notify',
    response_model=NotifyCountResponseSchema,
    summary='Notify current assignees about a group reminder',
)
async def notify_assignees(
    reminder_id: uuid.UUID,
    schema: GroupNotifyRequestSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> dict:
    """Send notification to all current assignees of a group reminder."""
    reminder = await _get_reminder_or_404(reminder_id, repos)
    group_service = GroupReminderService(repos=repos)

    count = await group_service.notify_assignees(
        reminder=reminder,
        sender=user,
        message=schema.message,
        scheduled_time=schema.scheduled_time,
    )
    return {'notified': count}


@router.post(
    '/reminders/{reminder_id}/notify-all',
    response_model=NotifyCountResponseSchema,
    summary='Notify ALL group members about a reminder (admin/owner only)',
    status_code=status.HTTP_200_OK,
)
async def notify_all_members(
    reminder_id: uuid.UUID,
    schema: GroupNotifyRequestSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> dict:
    """Admin/owner: send a notification to every member of the group."""
    reminder = await _get_reminder_or_404(reminder_id, repos)
    group_service = GroupReminderService(repos=repos)

    count = await group_service.notify_all_members(
        reminder=reminder,
        sender=user,
        message=schema.message,
        scheduled_time=schema.scheduled_time,
    )
    return {'notified': count}


@router.patch(
    '/reminders/{reminder_id}/group-update',
    response_model=RemindersResponseSchema,
    summary='Update a group reminder with role-based access control',
)
async def update_group_reminder(
    reminder_id: uuid.UUID,
    schema: GroupReminderUpdateRequestSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> dict:
    """Update a group reminder with Jira-style collaborative rules.

    - Admins/owners: can change all fields, optionally notify assignees
    - Creators: can change all fields
    - Assignees (member role): can only change status
    """
    reminder = await _get_reminder_or_404(reminder_id, repos)
    group_service = GroupReminderService(repos=repos)

    group_id = await group_service.ensure_group_reminder(reminder)
    membership = await group_service.ensure_group_member(group_id=group_id, user_id=user.id)

    payload = schema.model_dump(exclude_unset=True)
    notify_flag = payload.pop('notify_assignees_on_update', False)
    new_assignee_ids = payload.pop('assignee_ids', None)
    notify_assignees = payload.pop('notify_assignees', False)
    assignee_scheduled_time = payload.pop('assignee_scheduled_time', None)

    updated = await group_service.update_group_reminder(
        reminder=reminder,
        payload=payload,
        user=user,
        membership=membership,
        notify_assignees_on_update=notify_flag,
        new_assignee_ids=new_assignee_ids,
        notify_new_assignees=notify_assignees,
        assignee_scheduled_time=assignee_scheduled_time,
    )

    service = ReminderService(repos=repos)
    return await service.enrich_reminder_with_notification_info(updated)


@router.delete(
    '/reminders/{reminder_id}/assignees/user/{target_user_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a specific user from a group reminder's assignees (admin/owner)",
)
async def remove_group_assignee(
    reminder_id: uuid.UUID,
    target_user_id: uuid.UUID,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> None:
    """Remove a specific user from a group reminder's assignee list."""
    from app.exceptions import NotFoundError

    reminder = await _get_reminder_or_404(reminder_id, repos)
    group_service = GroupReminderService(repos=repos)
    group_id = await group_service.ensure_group_reminder(reminder)
    membership = await group_service.ensure_group_member(group_id=group_id, user_id=user.id)
    if membership.role not in (MemberRoles.ADMIN, MemberRoles.OWNER):
        from app.exceptions import AuthorizationError

        msg = 'Only admins and owners can remove assignees'
        raise AuthorizationError(msg)

    assignment = await repos.reminder_assignee_pgsql_repo.find_by_reminder_and_user(
        reminder_id=reminder_id,
        user_id=target_user_id,
    )
    if assignment is None:
        msg = 'Assignment not found'
        raise NotFoundError(msg)

    await repos.reminder_assignee_pgsql_repo.delete_by_id(assignee_id=assignment.id)
