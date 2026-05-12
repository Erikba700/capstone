import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.dependencies import get_current_user, get_repo, get_shared_tx_repo
from app.entities import UserEntity
from app.entities.reminder_assignee import ReminderAssigneeEntity
from app.exceptions import AuthorizationError, NotFoundError
from app.repos import RepoFactory
from app.schemas.group_schemas import (
    AddAssigneeRequestSchema,
    AssigneeResponseSchema,
    CompleteAssignmentRequestSchema,
)
from app.services.group_service import GroupService

router = APIRouter(tags=['Reminder Assignees'])


@router.get('/reminders/{reminder_id}/assignees', response_model=list[AssigneeResponseSchema])
async def list_assignees(
    reminder_id: uuid.UUID,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_repo)],
) -> object:
    """List all assignees for a reminder."""
    return await repos.reminder_assignee_pgsql_repo.list_by_reminder_id(reminder_id=reminder_id)


@router.post(
    '/reminders/{reminder_id}/assignees',
    response_model=AssigneeResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def add_assignee(
    reminder_id: uuid.UUID,
    schema: AddAssigneeRequestSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> object:
    """Add an assignee to a reminder. Caller must be admin/owner of the reminder's group."""
    reminder = await repos.reminder_pgsql_repo.find_by_id(reminder_id=reminder_id)
    if reminder is None:
        msg = 'Reminder not found'
        raise NotFoundError(msg)

    # Verify caller is admin/owner if it's a group reminder
    if reminder.group_id is not None:
        service = GroupService(repos=repos)
        await service.require_admin(group_id=reminder.group_id, user_id=user.id)
        # Verify assignee is a group member
        membership = await service.get_membership(group_id=reminder.group_id, user_id=schema.user_id)
        if membership is None:
            msg = 'Cannot assign a user who is not a group member'
            raise AuthorizationError(msg)
    elif reminder.owner_id != user.id:
        msg = 'Only the reminder owner can add assignees'
        raise AuthorizationError(msg)

    entity = ReminderAssigneeEntity.create_new(
        reminder_id=reminder_id,
        user_id=schema.user_id,
        assigned_by=user.id,
    )
    return await repos.reminder_assignee_pgsql_repo.insert(entity=entity)


@router.patch('/reminder-assignments/{assignment_id}', response_model=AssigneeResponseSchema)
async def update_assignment(
    assignment_id: uuid.UUID,
    schema: CompleteAssignmentRequestSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> object:
    """Mark a reminder assignment as completed. Assignee or group admin/owner."""
    assignment = await repos.reminder_assignee_pgsql_repo.find_by_id(assignee_id=assignment_id)
    if assignment is None:
        msg = 'Assignment not found'
        raise NotFoundError(msg)

    # Assignee can always complete their own; admin/owner can complete for anyone
    if assignment.user_id != user.id:
        reminder = await repos.reminder_pgsql_repo.find_by_id(reminder_id=assignment.reminder_id)
        if reminder and reminder.group_id:
            service = GroupService(repos=repos)
            await service.require_admin(group_id=reminder.group_id, user_id=user.id)
        else:
            msg = 'Only the assignee can update this assignment'
            raise AuthorizationError(msg)

    from datetime import UTC, datetime

    updated = assignment.model_copy(
        update={
            'completed_at': datetime.now(UTC) if schema.completed else None,
            'updated_at': assignment.generate_current_timestamp(),
        }
    )
    return await repos.reminder_assignee_pgsql_repo.update(entity=updated)


@router.delete('/reminder-assignments/{assignment_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(
    assignment_id: uuid.UUID,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> None:
    """Delete a reminder assignment. Requires group admin/owner or reminder owner."""
    assignment = await repos.reminder_assignee_pgsql_repo.find_by_id(assignee_id=assignment_id)
    if assignment is None:
        msg = 'Assignment not found'
        raise NotFoundError(msg)

    reminder = await repos.reminder_pgsql_repo.find_by_id(reminder_id=assignment.reminder_id)
    if reminder and reminder.group_id:
        service = GroupService(repos=repos)
        await service.require_admin(group_id=reminder.group_id, user_id=user.id)
    elif reminder and reminder.owner_id != user.id:
        msg = 'Only the reminder owner can remove assignees'
        raise AuthorizationError(msg)

    await repos.reminder_assignee_pgsql_repo.delete_by_id(assignee_id=assignment_id)
