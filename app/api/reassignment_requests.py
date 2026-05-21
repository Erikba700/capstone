"""API router for group reassignment requests."""

import uuid
from datetime import UTC, datetime
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends

from app.dependencies import get_current_user, get_shared_tx_repo
from app.entities import NotificationEntity, UserEntity
from app.exceptions import AuthorizationError, BadRequestError, NotFoundError
from app.repos import RepoFactory
from app.schemas.base_schemas import BaseSchema
from app.services.notifications_service import NotificationService

logger = structlog.getLogger(__name__)

router = APIRouter(tags=['Reassignment Requests'])


# ── Schemas ───────────────────────────────────────────────────────────────────


class CreateReassignmentRequestSchema(BaseSchema):
    """Body for requesting to take over an assignment."""

    reminder_id: uuid.UUID
    message: str | None = None


class ReassignmentRequestResponseSchema(BaseSchema):
    """Response shape for a reassignment request."""

    id: uuid.UUID
    reminder_id: uuid.UUID
    requester_id: uuid.UUID
    requester_name: str | None = None
    current_assignee_id: uuid.UUID
    status: str
    message: str | None = None
    reminder_title: str | None = None
    created_at: datetime


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _enrich(repos: RepoFactory, entity_id: uuid.UUID) -> dict:
    """Return a response dict with requester name and reminder title."""
    from app.repos.reassignment_request_pgsql_repo import ReassignmentRequestPgsqlRepo

    repo: ReassignmentRequestPgsqlRepo = repos.reassignment_request_pgsql_repo
    entity = await repo.find_by_id(entity_id)
    if entity is None:
        return {}
    requester = await repos.user_pgsql_repo.find_by_id(entity.requester_id)
    reminder = await repos.reminder_pgsql_repo.find_by_id(entity.reminder_id)
    return {
        **entity.model_dump(),
        'requester_name': requester.name if requester else None,
        'reminder_title': reminder.title if reminder else None,
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post(
    '/reassignment-requests',
    response_model=ReassignmentRequestResponseSchema,
    summary='Request to take over a group reminder assignment',
)
async def create_reassignment_request(
    schema: CreateReassignmentRequestSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> dict:
    """A group member asks to take over another member's reminder.

    - Requester must be a group member.
    - Reminder must belong to a group.
    - There must be an active (non-completed) assignee other than the requester.
    - Notifies the current assignee via email.
    """
    from app.entities.reassignment_request import ReassignmentRequestEntity

    reminder = await repos.reminder_pgsql_repo.find_by_id(schema.reminder_id)
    if reminder is None:
        msg = 'Reminder not found'
        raise NotFoundError(msg)
    if reminder.group_id is None:
        msg = 'Reassignment requests are only for group reminders'
        raise BadRequestError(msg)

    # Verify requester is a group member
    membership = await repos.group_member_pgsql_repo.find_by_group_and_user(
        group_id=reminder.group_id,
        user_id=user.id,
    )
    if membership is None:
        msg = 'You are not a member of this group'
        raise AuthorizationError(msg)

    # Find current assignee (first non-completed, non-self)
    assignments = await repos.reminder_assignee_pgsql_repo.list_by_reminder_id(
        reminder_id=reminder.id,
    )
    current = next(
        (a for a in assignments if a.user_id != user.id and a.completed_at is None),
        None,
    )
    if current is None:
        msg = 'No active assignee to request a takeover from'
        raise BadRequestError(msg)

    # Prevent duplicate pending requests
    existing = await repos.reassignment_request_pgsql_repo.find_existing_pending(
        reminder_id=reminder.id,
        requester_id=user.id,
    )
    if existing is not None:
        msg = 'You already have a pending reassignment request for this reminder'
        raise BadRequestError(msg)

    entity = ReassignmentRequestEntity.create_new(
        reminder_id=reminder.id,
        requester_id=user.id,
        current_assignee_id=current.user_id,
        message=schema.message,
    )
    created = await repos.reassignment_request_pgsql_repo.insert(entity)
    logger.info('Created reassignment request', id=created.id, reminder_id=reminder.id)

    # Notify current assignee
    assignee_user = await repos.user_pgsql_repo.find_by_id(current.user_id)
    if assignee_user is not None:
        notif_msg = f'{user.name} wants to take over your assignment for "{reminder.title}"' + (
            f': {schema.message}' if schema.message else ''
        )
        notification = NotificationEntity.create_new(
            user_id=assignee_user.id,
            reminder_id=reminder.id,
            message=notif_msg,
            creator_email=user.email,
        )
        svc = NotificationService(repos=repos)
        created_notif = await repos.notification_pgsql_repo.insert(notification)
        success = await svc.send_custom_notification(
            recipient=assignee_user.email,
            subject=f'Takeover request: {reminder.title}',
            message=(
                f'Hi {assignee_user.name},\n\n{notif_msg}\n\n'
                f'Log in to Remindly to accept or reject this request.\n\n— Remindly'
            ),
        )
        if success:
            await svc.mark_notification_as_sent(created_notif)

    return await _enrich(repos, created.id)


@router.get(
    '/reassignment-requests/incoming',
    response_model=list[ReassignmentRequestResponseSchema],
    summary='List pending reassignment requests directed at me',
)
async def list_incoming_requests(
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> list[dict]:
    """Return all pending requests where the current user is the assignee."""
    requests = await repos.reassignment_request_pgsql_repo.list_pending_for_assignee(
        assignee_id=user.id,
    )
    result = []
    for req in requests:
        requester = await repos.user_pgsql_repo.find_by_id(req.requester_id)
        reminder = await repos.reminder_pgsql_repo.find_by_id(req.reminder_id)
        result.append(
            {
                **req.model_dump(),
                'requester_name': requester.name if requester else None,
                'reminder_title': reminder.title if reminder else None,
            }
        )
    return result


@router.post(
    '/reassignment-requests/{request_id}/accept',
    response_model=ReassignmentRequestResponseSchema,
    summary='Accept a reassignment request — transfer the assignment',
)
async def accept_reassignment_request(
    request_id: uuid.UUID,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> dict:
    """Accept: remove current assignment, add requester, notify requester."""
    from app.entities.reminder_assignee import ReminderAssigneeEntity

    req = await repos.reassignment_request_pgsql_repo.find_by_id(request_id)
    if req is None:
        msg = 'Request not found'
        raise NotFoundError(msg)
    if req.current_assignee_id != user.id:
        msg = 'Only the current assignee can accept this request'
        raise AuthorizationError(msg)
    if req.status != 'pending':
        msg = f'Request is already {req.status}'
        raise BadRequestError(msg)

    now = datetime.now(UTC)

    # Resolve request
    resolved = req.model_copy(update={'status': 'accepted', 'resolved_at': now, 'updated_at': now})
    await repos.reassignment_request_pgsql_repo.update(resolved)

    reminder = await repos.reminder_pgsql_repo.find_by_id(req.reminder_id)
    if reminder is None:
        msg = 'Reminder not found'
        raise NotFoundError(msg)

    # Remove the current user's assignment
    my_assignment = await repos.reminder_assignee_pgsql_repo.find_by_reminder_and_user(
        reminder_id=req.reminder_id,
        user_id=user.id,
    )
    if my_assignment is not None:
        await repos.reminder_assignee_pgsql_repo.delete_by_id(assignee_id=my_assignment.id)

    # Remove any existing assignment for the requester to avoid duplicates
    existing_requester_assignment = await repos.reminder_assignee_pgsql_repo.find_by_reminder_and_user(
        reminder_id=req.reminder_id,
        user_id=req.requester_id,
    )
    if existing_requester_assignment is not None:
        await repos.reminder_assignee_pgsql_repo.delete_by_id(assignee_id=existing_requester_assignment.id)

    # Create assignment for requester
    new_entity = ReminderAssigneeEntity.create_new(
        reminder_id=req.reminder_id,
        user_id=req.requester_id,
        assigned_by=user.id,
    )
    await repos.reminder_assignee_pgsql_repo.insert(entity=new_entity)

    # Notify requester
    requester = await repos.user_pgsql_repo.find_by_id(req.requester_id)
    if requester is not None and reminder is not None:
        msg_text = f'{user.name} accepted your takeover request for "{reminder.title}"'
        notification = NotificationEntity.create_new(
            user_id=requester.id,
            reminder_id=reminder.id,
            message=msg_text,
            creator_email=user.email,
        )
        svc = NotificationService(repos=repos)
        created_notif = await repos.notification_pgsql_repo.insert(notification)
        success = await svc.send_custom_notification(
            recipient=requester.email,
            subject=f'Takeover accepted: {reminder.title}',
            message=f'Hi {requester.name},\n\n{msg_text}\n\nYou are now assigned.\n\n— Remindly',
        )
        if success:
            await svc.mark_notification_as_sent(created_notif)

    return await _enrich(repos, req.id)


@router.post(
    '/reassignment-requests/{request_id}/reject',
    response_model=ReassignmentRequestResponseSchema,
    summary='Reject a reassignment request',
)
async def reject_reassignment_request(
    request_id: uuid.UUID,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> dict:
    """Reject: mark request rejected and notify the requester."""
    req = await repos.reassignment_request_pgsql_repo.find_by_id(request_id)
    if req is None:
        msg = 'Request not found'
        raise NotFoundError(msg)
    if req.current_assignee_id != user.id:
        msg = 'Only the current assignee can reject this request'
        raise AuthorizationError(msg)
    if req.status != 'pending':
        msg = f'Request is already {req.status}'
        raise BadRequestError(msg)

    now = datetime.now(UTC)
    resolved = req.model_copy(update={'status': 'rejected', 'resolved_at': now, 'updated_at': now})
    await repos.reassignment_request_pgsql_repo.update(resolved)

    # Notify requester
    reminder = await repos.reminder_pgsql_repo.find_by_id(req.reminder_id)
    requester = await repos.user_pgsql_repo.find_by_id(req.requester_id)
    if requester is not None and reminder is not None:
        msg_text = f'{user.name} rejected your takeover request for "{reminder.title}"'
        notification = NotificationEntity.create_new(
            user_id=requester.id,
            reminder_id=reminder.id,
            message=msg_text,
            creator_email=user.email,
        )
        svc = NotificationService(repos=repos)
        created_notif = await repos.notification_pgsql_repo.insert(notification)
        success = await svc.send_custom_notification(
            recipient=requester.email,
            subject=f'Takeover rejected: {reminder.title}',
            message=f'Hi {requester.name},\n\n{msg_text}\n\n— Remindly',
        )
        if success:
            await svc.mark_notification_as_sent(created_notif)

    return await _enrich(repos, req.id)
