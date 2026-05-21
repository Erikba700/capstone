import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import RedirectResponse

from app.dependencies import get_current_user, get_repo, get_shared_tx_repo
from app.entities import NotificationEntity, UserEntity
from app.entities.friendship import FriendshipStatus
from app.entities.reminder_assignee import ReminderAssigneeEntity
from app.exceptions import AuthorizationError, BadRequestError, NotFoundError
from app.repos import RepoFactory
from app.schemas.group_schemas import (
    AcknowledgeResponseSchema,
    AddAssigneeRequestSchema,
    AssigneeResponseSchema,
    CompleteAssignmentRequestSchema,
    CompleteResponseSchema,
)
from app.services.group_service import GroupService
from app.services.notifications_service import NotificationService

router = APIRouter(tags=['Reminder Assignees'])


# ── Public callback (no auth, for email links) ──────────────────────────────


@router.get(
    '/reminder-assignments/callback',
    summary='Email callback: acknowledge or complete via signed token',
    include_in_schema=True,
)
async def assignment_callback(
    token: Annotated[str, Query()],
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> RedirectResponse:
    """Decode a signed callback token and perform acknowledge/complete action.

    Redirects to the frontend page with status query param.
    """
    from app.config import settings
    from app.utils.callback_tokens import decode_callback_token

    try:
        payload = decode_callback_token(token)
    except ValueError:
        return RedirectResponse(
            url=f'{settings.frontend_url}/reminder-callback?status=error&reason=invalid_token',
            status_code=302,
        )

    try:
        assignment_id = uuid.UUID(payload['sub'])
        user_id = uuid.UUID(payload['uid'])
        action: str = payload['act']
    except (KeyError, ValueError):
        return RedirectResponse(
            url=f'{settings.frontend_url}/reminder-callback?status=error&reason=malformed_token',
            status_code=302,
        )

    assignment = await repos.reminder_assignee_pgsql_repo.find_by_id(assignee_id=assignment_id)
    if assignment is None or assignment.user_id != user_id:
        return RedirectResponse(
            url=f'{settings.frontend_url}/reminder-callback?status=error&reason=not_found',
            status_code=302,
        )

    now = datetime.now(UTC)

    if action == 'acknowledge':
        if assignment.acknowledged_at is not None:
            # Already acknowledged - just redirect nicely
            return RedirectResponse(
                url=f'{settings.frontend_url}/reminder-callback?status=already_done&action=acknowledge',
                status_code=302,
            )
        updated = assignment.acknowledge()
        updated = await repos.reminder_assignee_pgsql_repo.update(entity=updated)
        await _update_reminder_status(repos, assignment.reminder_id, 'in_progress')
        # Stamp is_read_at on all unread notifications for this assignment user+reminder
        await _stamp_is_read_at(repos, assignment.user_id, assignment.reminder_id, now)
        await _notify_assigner(repos, updated, 'acknowledged')
        return RedirectResponse(
            url=f'{settings.frontend_url}/reminder-callback?status=success&action=acknowledge',
            status_code=302,
        )

    elif action == 'complete':
        if assignment.completed_at is not None:
            return RedirectResponse(
                url=f'{settings.frontend_url}/reminder-callback?status=already_done&action=complete',
                status_code=302,
            )
        updated = assignment.complete()
        if updated.acknowledged_at is None:
            updated = updated.model_copy(update={'acknowledged_at': now, 'updated_at': now})
        updated = await repos.reminder_assignee_pgsql_repo.update(entity=updated)
        await _update_reminder_status(repos, assignment.reminder_id, 'completed')
        await _stamp_is_read_at(repos, assignment.user_id, assignment.reminder_id, now)
        await _notify_assigner(repos, updated, 'completed')
        return RedirectResponse(
            url=f'{settings.frontend_url}/reminder-callback?status=success&action=complete',
            status_code=302,
        )

    return RedirectResponse(
        url=f'{settings.frontend_url}/reminder-callback?status=error&reason=unknown_action',
        status_code=302,
    )


# ── Authenticated endpoints ──────────────────────────────────────────────────


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

    if reminder.group_id is not None:
        service = GroupService(repos=repos)
        await service.require_admin(group_id=reminder.group_id, user_id=user.id)
        membership = await service.get_membership(group_id=reminder.group_id, user_id=schema.user_id)
        if membership is None:
            msg = 'Cannot assign a user who is not a group member'
            raise AuthorizationError(msg)
    elif reminder.owner_id != user.id:
        msg = 'Only the reminder owner can add assignees'
        raise AuthorizationError(msg)
    elif schema.user_id != user.id:
        friendship = await repos.friendship_pgsql_repo.find_between_users(
            user_a=user.id,
            user_b=schema.user_id,
        )
        if friendship is None or friendship.status != FriendshipStatus.ACCEPTED:
            msg = 'You can only assign personal reminders to accepted friends'
            raise AuthorizationError(msg)

    entity = ReminderAssigneeEntity.create_new(
        reminder_id=reminder_id,
        user_id=schema.user_id,
        assigned_by=user.id,
    )
    result = await repos.reminder_assignee_pgsql_repo.insert(entity=entity)
    await _notify_assignee(
        repos, reminder_id=reminder_id, assignee_id=schema.user_id, assigner=user, assignment_id=result.id
    )
    return result


@router.post(
    '/reminder-assignments/{assignment_id}/acknowledge',
    response_model=AcknowledgeResponseSchema,
)
async def acknowledge_assignment(
    assignment_id: uuid.UUID,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> dict:
    """Acknowledge a reminder assignment (mark as seen → IN_PROGRESS).

    Only the assigned user can acknowledge their own assignment.
    """
    assignment = await repos.reminder_assignee_pgsql_repo.find_by_id(assignee_id=assignment_id)
    if assignment is None:
        msg = 'Assignment not found'
        raise NotFoundError(msg)
    if assignment.user_id != user.id:
        msg = 'Only the assignee can acknowledge this assignment'
        raise AuthorizationError(msg)
    if assignment.acknowledged_at is not None:
        msg = 'Assignment already acknowledged'
        raise BadRequestError(msg)

    now = datetime.now(UTC)
    updated = assignment.acknowledge()
    updated = await repos.reminder_assignee_pgsql_repo.update(entity=updated)
    await _update_reminder_status(repos, assignment.reminder_id, 'in_progress')
    await _stamp_is_read_at(repos, user.id, assignment.reminder_id, now)
    await _notify_assigner(repos, updated, 'acknowledged')

    return {
        'id': updated.id,
        'status': 'in_progress',
        'acknowledged_at': updated.acknowledged_at,
        'is_read_at': now,
    }


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

    if assignment.user_id != user.id:
        reminder = await repos.reminder_pgsql_repo.find_by_id(reminder_id=assignment.reminder_id)
        if reminder and reminder.group_id:
            service = GroupService(repos=repos)
            await service.require_admin(group_id=reminder.group_id, user_id=user.id)
        else:
            msg = 'Only the assignee can update this assignment'
            raise AuthorizationError(msg)

    now = datetime.now(UTC)
    updated = assignment.model_copy(
        update={
            'completed_at': now if schema.completed else None,
            'updated_at': assignment.generate_current_timestamp(),
        }
    )
    # Ensure acknowledged_at is set when completing
    if schema.completed and updated.acknowledged_at is None:
        updated = updated.model_copy(update={'acknowledged_at': now})

    result = await repos.reminder_assignee_pgsql_repo.update(entity=updated)
    if schema.completed:
        await _update_reminder_status(repos, assignment.reminder_id, 'completed')
        await _stamp_is_read_at(repos, assignment.user_id, assignment.reminder_id, now)
        await _notify_assigner(repos, result, 'completed')
    return result


@router.post(
    '/reminder-assignments/{assignment_id}/complete',
    response_model=CompleteResponseSchema,
)
async def complete_assignment(
    assignment_id: uuid.UUID,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> dict:
    """Complete a reminder assignment → COMPLETED.

    Sets completed_at and is_read_at, notifies the assigner.
    """
    assignment = await repos.reminder_assignee_pgsql_repo.find_by_id(assignee_id=assignment_id)
    if assignment is None:
        msg = 'Assignment not found'
        raise NotFoundError(msg)
    if assignment.user_id != user.id:
        msg = 'Only the assignee can complete this assignment'
        raise AuthorizationError(msg)
    if assignment.completed_at is not None:
        msg = 'Assignment already completed'
        raise BadRequestError(msg)

    now = datetime.now(UTC)
    updated = assignment.complete()
    if updated.acknowledged_at is None:
        updated = updated.model_copy(update={'acknowledged_at': now, 'updated_at': now})
    updated = await repos.reminder_assignee_pgsql_repo.update(entity=updated)
    await _update_reminder_status(repos, assignment.reminder_id, 'completed')
    await _stamp_is_read_at(repos, user.id, assignment.reminder_id, now)
    await _notify_assigner(repos, updated, 'completed')

    return {
        'id': updated.id,
        'status': 'completed',
        'completed_at': updated.completed_at,
        'is_read_at': now,
    }


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


# ── Helpers ──────────────────────────────────────────────────────────────────


async def _update_reminder_status(
    repos: RepoFactory,
    reminder_id: uuid.UUID,
    new_status: str,
) -> None:
    """Update the reminder's status, but only if the transition makes sense.

    - 'in_progress': only upgrades from 'pending'
    - 'completed': always sets (overrides pending/in_progress)
    """
    from app.entities.reminder import ReminderStatus

    reminder = await repos.reminder_pgsql_repo.find_by_id(reminder_id=reminder_id)
    if reminder is None:
        return
    if new_status == 'completed':
        if reminder.status == ReminderStatus.COMPLETED:
            return
        updated = reminder.model_copy(
            update={
                'status': ReminderStatus.COMPLETED,
                'updated_at': reminder.generate_current_timestamp(),
            }
        )
        await repos.reminder_pgsql_repo.update(entity=updated)
    elif new_status == 'in_progress':
        if reminder.status != ReminderStatus.PENDING:
            return
        updated = reminder.model_copy(
            update={
                'status': ReminderStatus.IN_PROGRESS,
                'updated_at': reminder.generate_current_timestamp(),
            }
        )
        await repos.reminder_pgsql_repo.update(entity=updated)


async def _stamp_is_read_at(
    repos: RepoFactory,
    user_id: uuid.UUID,
    reminder_id: uuid.UUID,
    now: datetime,
) -> None:
    """Set is_read_at on unread notifications for user+reminder."""
    notifications = await repos.notification_pgsql_repo.fetch_notifications_by_reminder_id(
        reminder_id=reminder_id,
    )
    for notif in notifications:
        if notif.user_id == user_id and notif.is_read_at is None:
            updated = notif.update({'is_read_at': now})
            await repos.notification_pgsql_repo.update(entity=updated)


async def _notify_assignee(
    repos: RepoFactory,
    reminder_id: uuid.UUID,
    assignee_id: uuid.UUID,
    assigner: UserEntity,
    assignment_id: uuid.UUID | None = None,
) -> None:
    """Create an in-app notification (and send email with action buttons) to the new assignee."""
    reminder = await repos.reminder_pgsql_repo.find_by_id(reminder_id=reminder_id)
    assignee = await repos.user_pgsql_repo.find_by_id(assignee_id)
    if reminder is None or assignee is None:
        return

    msg = f'{assigner.name} assigned you a reminder: "{reminder.title}"'
    notification = NotificationEntity.create_new(
        user_id=assignee_id,
        reminder_id=reminder_id,
        message=msg,
        creator_email=assigner.email,
    )
    notification_service = NotificationService(repos=repos)
    created = await repos.notification_pgsql_repo.insert(notification)

    if assignment_id is not None:
        success = await notification_service.send_reminder_notification_with_actions(
            user=assignee,
            reminder=reminder,
            notification=created,
            assignment_id=assignment_id,
        )
    else:
        success = await notification_service.send_custom_notification(
            recipient=assignee.email,
            subject=f'New reminder assigned to you: {reminder.title}',
            message=f'Hi {assignee.name},\n\n{msg}\n\n— Remindly',
        )
    if success:
        await notification_service.mark_notification_as_sent(created)


async def _notify_assigner(
    repos: RepoFactory,
    assignment: ReminderAssigneeEntity,
    action: str,
) -> None:
    """Create and send a notification to the reminder assigner about this action."""
    reminder = await repos.reminder_pgsql_repo.find_by_id(reminder_id=assignment.reminder_id)
    if reminder is None:
        return

    assigner_id = assignment.assigned_by
    assigner = await repos.user_pgsql_repo.find_by_id(assigner_id)
    assignee = await repos.user_pgsql_repo.find_by_id(assignment.user_id)
    if assigner is None or assignee is None:
        return

    action_verb = 'acknowledged' if action == 'acknowledged' else 'completed'
    msg = f'{assignee.name} {action_verb} reminder "{reminder.title}"'

    notification = NotificationEntity.create_new(
        user_id=assigner_id,
        reminder_id=reminder.id,
        message=msg,
        creator_email=assignee.email,
    )
    notification_service = NotificationService(repos=repos)
    created = await repos.notification_pgsql_repo.insert(notification)
    success = await notification_service.send_custom_notification(
        recipient=assigner.email,
        subject=f'Reminder {action_verb}: {reminder.title}',
        message=f'Hi {assigner.name},\n\n{msg}\n\n— Remindly',
    )
    if success:
        await notification_service.mark_notification_as_sent(created)
