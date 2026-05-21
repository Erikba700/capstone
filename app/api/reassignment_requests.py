"""API router for group reassignment requests."""

import uuid
from datetime import UTC, datetime
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse

from app.dependencies import get_current_user, get_shared_tx_repo
from app.entities import NotificationEntity, UserEntity
from app.exceptions import AuthorizationError, BadRequestError, NotFoundError
from app.repos import RepoFactory
from app.schemas.base_schemas import BaseSchema
from app.services.notifications_service import NotificationService

logger = structlog.getLogger(__name__)
router = APIRouter(tags=['Reassignment Requests'])


# -- Schemas ------------------------------------------------------------------
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


# -- Helpers ------------------------------------------------------------------
async def _enrich(repos: RepoFactory, entity_id: uuid.UUID) -> dict:
    """Return a response dict with requester name and reminder title."""
    entity = await repos.reassignment_request_pgsql_repo.find_by_id(entity_id)
    if entity is None:
        return {}
    requester = await repos.user_pgsql_repo.find_by_id(entity.requester_id)
    reminder = await repos.reminder_pgsql_repo.find_by_id(entity.reminder_id)
    return {
        **entity.model_dump(),
        'requester_name': requester.name if requester else None,
        'reminder_title': reminder.title if reminder else None,
    }


def _build_reassignment_email_html(
    assignee_name: str,
    requester_name: str,
    reminder_title: str,
    optional_message: str | None,
    accept_url: str,
    reject_url: str,
) -> str:
    """Build HTML email body with Accept/Reject action buttons."""
    msg_html = (
        f'<p style="color:#555;font-size:14px;font-style:italic;">"{optional_message}"</p>' if optional_message else ''
    )
    return (
        '<!DOCTYPE html><html><body style="font-family:Arial,sans-serif;'
        'background:#f9fafb;padding:32px;">'
        '<div style="max-width:540px;margin:0 auto;background:#fff;border-radius:12px;'
        'padding:32px;box-shadow:0 2px 8px rgba(0,0,0,0.08);">'
        f'<h2 style="color:#7c3aed;margin-top:0;">&#x1F504; Takeover Request</h2>'
        f'<p style="color:#374151;font-size:15px;">Hi {assignee_name},</p>'
        f'<p style="color:#374151;font-size:14px;">'
        f'<strong>{requester_name}</strong> wants to take over your assignment for '
        f'<strong>"{reminder_title}"</strong>.</p>'
        f'{msg_html}'
        '<div style="margin:28px 0;">'
        f'<a href="{accept_url}" style="display:inline-block;padding:12px 24px;'
        'background:#16a34a;color:#fff;text-decoration:none;border-radius:8px;'
        'font-weight:bold;font-size:14px;">&#10003; Accept Takeover</a>'
        f'<a href="{reject_url}" style="display:inline-block;padding:12px 24px;'
        'background:#dc2626;color:#fff;text-decoration:none;border-radius:8px;'
        'font-weight:bold;font-size:14px;margin-left:12px;">&#10007; Reject</a>'
        '</div>'
        '<p style="color:#9ca3af;font-size:11px;margin-top:24px;">'
        'These links expire in 7 days. Only you can use them.</p>'
        '<p style="color:#9ca3af;font-size:11px;">&#8212; Remindly</p>'
        '</div></body></html>'
    )


async def _do_accept(
    repos: RepoFactory,
    request_id: uuid.UUID,
    assignee_id: uuid.UUID,
) -> None:
    """Transfer the assignment from current assignee to requester."""
    from app.entities.reminder_assignee import ReminderAssigneeEntity

    req = await repos.reassignment_request_pgsql_repo.find_by_id(request_id)
    if req is None:
        return
    now = datetime.now(UTC)
    resolved = req.model_copy(update={'status': 'accepted', 'resolved_at': now, 'updated_at': now})
    await repos.reassignment_request_pgsql_repo.update(resolved)
    my_asgn = await repos.reminder_assignee_pgsql_repo.find_by_reminder_and_user(
        reminder_id=req.reminder_id,
        user_id=assignee_id,
    )
    if my_asgn is not None:
        await repos.reminder_assignee_pgsql_repo.delete_by_id(assignee_id=my_asgn.id)
    existing = await repos.reminder_assignee_pgsql_repo.find_by_reminder_and_user(
        reminder_id=req.reminder_id,
        user_id=req.requester_id,
    )
    if existing is not None:
        await repos.reminder_assignee_pgsql_repo.delete_by_id(assignee_id=existing.id)
    new_entity = ReminderAssigneeEntity.create_new(
        reminder_id=req.reminder_id,
        user_id=req.requester_id,
        assigned_by=assignee_id,
    )
    await repos.reminder_assignee_pgsql_repo.insert(entity=new_entity)
    reminder = await repos.reminder_pgsql_repo.find_by_id(req.reminder_id)
    requester = await repos.user_pgsql_repo.find_by_id(req.requester_id)
    assignee_user = await repos.user_pgsql_repo.find_by_id(assignee_id)
    if requester and reminder and assignee_user:
        msg_text = f'{assignee_user.name} accepted your takeover request for "{reminder.title}"'
        notification = NotificationEntity.create_new(
            user_id=requester.id,
            reminder_id=reminder.id,
            message=msg_text,
            creator_email=assignee_user.email,
        )
        svc = NotificationService(repos=repos)
        created_notif = await repos.notification_pgsql_repo.insert(notification)
        success = await svc.send_custom_notification(
            recipient=requester.email,
            subject=f'Takeover accepted: {reminder.title}',
            message=f'Hi {requester.name},\n\n{msg_text}\n\nYou are now assigned.\n\n--- Remindly',
        )
        if success:
            await svc.mark_notification_as_sent(created_notif)


async def _do_reject(
    repos: RepoFactory,
    request_id: uuid.UUID,
    assignee_id: uuid.UUID,
) -> None:
    """Mark request rejected and notify the requester."""
    req = await repos.reassignment_request_pgsql_repo.find_by_id(request_id)
    if req is None:
        return
    now = datetime.now(UTC)
    resolved = req.model_copy(update={'status': 'rejected', 'resolved_at': now, 'updated_at': now})
    await repos.reassignment_request_pgsql_repo.update(resolved)
    reminder = await repos.reminder_pgsql_repo.find_by_id(req.reminder_id)
    requester = await repos.user_pgsql_repo.find_by_id(req.requester_id)
    assignee_user = await repos.user_pgsql_repo.find_by_id(assignee_id)
    if requester and reminder and assignee_user:
        msg_text = f'{assignee_user.name} rejected your takeover request for "{reminder.title}"'
        notification = NotificationEntity.create_new(
            user_id=requester.id,
            reminder_id=reminder.id,
            message=msg_text,
            creator_email=assignee_user.email,
        )
        svc = NotificationService(repos=repos)
        created_notif = await repos.notification_pgsql_repo.insert(notification)
        success = await svc.send_custom_notification(
            recipient=requester.email,
            subject=f'Takeover rejected: {reminder.title}',
            message=f'Hi {requester.name},\n\n{msg_text}\n\n--- Remindly',
        )
        if success:
            await svc.mark_notification_as_sent(created_notif)


# -- Public email callback (no auth) -----------------------------------------
@router.get(
    '/reassignment-requests/callback',
    summary='Email callback: accept or reject a reassignment request via signed token',
    include_in_schema=True,
)
async def reassignment_callback(
    token: Annotated[str, Query()],
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> RedirectResponse:
    """Decode signed token and perform accept/reject, then redirect to frontend."""
    from app.config import settings
    from app.utils.callback_tokens import decode_reassignment_token

    frontend_url = settings.frontend_url
    try:
        payload = decode_reassignment_token(token)
    except ValueError:
        return RedirectResponse(
            url=f'{frontend_url}/reminder-callback?status=error&reason=invalid_token',
            status_code=302,
        )
    try:
        request_id = uuid.UUID(payload['sub'])
        assignee_id = uuid.UUID(payload['uid'])
        action: str = payload['act']
    except (KeyError, ValueError):
        return RedirectResponse(
            url=f'{frontend_url}/reminder-callback?status=error&reason=malformed_token',
            status_code=302,
        )
    req = await repos.reassignment_request_pgsql_repo.find_by_id(request_id)
    if req is None or req.current_assignee_id != assignee_id:
        return RedirectResponse(
            url=f'{frontend_url}/reminder-callback?status=error&reason=not_found',
            status_code=302,
        )
    if req.status != 'pending':
        return RedirectResponse(
            url=f'{frontend_url}/reminder-callback?status=already_done&action=takeover_{action}',
            status_code=302,
        )
    if action == 'accept':
        await _do_accept(repos, request_id, assignee_id)
        return RedirectResponse(
            url=f'{frontend_url}/reminder-callback?status=success&action=takeover_accept',
            status_code=302,
        )
    if action == 'reject':
        await _do_reject(repos, request_id, assignee_id)
        return RedirectResponse(
            url=f'{frontend_url}/reminder-callback?status=success&action=takeover_reject',
            status_code=302,
        )
    return RedirectResponse(
        url=f'{frontend_url}/reminder-callback?status=error&reason=unknown_action',
        status_code=302,
    )


# -- Authenticated endpoints --------------------------------------------------
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
    """A group member asks to take over another member's reminder."""
    from app.config import settings
    from app.entities.reassignment_request import ReassignmentRequestEntity
    from app.utils.callback_tokens import generate_reassignment_token

    reminder = await repos.reminder_pgsql_repo.find_by_id(schema.reminder_id)
    if reminder is None:
        msg = 'Reminder not found'
        raise NotFoundError(msg)
    if reminder.group_id is None:
        msg = 'Reassignment requests are only for group reminders'
        raise BadRequestError(msg)
    membership = await repos.group_member_pgsql_repo.find_by_group_and_user(
        group_id=reminder.group_id,
        user_id=user.id,
    )
    if membership is None:
        msg = 'You are not a member of this group'
        raise AuthorizationError(msg)
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
    assignee_user = await repos.user_pgsql_repo.find_by_id(current.user_id)
    if assignee_user is not None:
        backend_url = settings.backend_url
        accept_token = generate_reassignment_token(created.id, assignee_user.id, 'accept')
        reject_token = generate_reassignment_token(created.id, assignee_user.id, 'reject')
        accept_url = f'{backend_url}/reassignment-requests/callback?token={accept_token}'
        reject_url = f'{backend_url}/reassignment-requests/callback?token={reject_token}'
        html_body = _build_reassignment_email_html(
            assignee_name=assignee_user.name,
            requester_name=user.name,
            reminder_title=reminder.title,
            optional_message=schema.message,
            accept_url=accept_url,
            reject_url=reject_url,
        )
        plain_body = (
            f'Hi {assignee_user.name},\n\n'
            f'{user.name} wants to take over your assignment for "{reminder.title}"'
            + (f': {schema.message}' if schema.message else '')
            + f'\n\nAccept: {accept_url}\nReject: {reject_url}\n\n--- Remindly'
        )
        notification = NotificationEntity.create_new(
            user_id=assignee_user.id,
            reminder_id=reminder.id,
            message=f'{user.name} wants to take over your assignment for "{reminder.title}"',
            creator_email=user.email,
        )
        svc = NotificationService(repos=repos)
        created_notif = await repos.notification_pgsql_repo.insert(notification)
        success = await svc.send_custom_notification(
            recipient=assignee_user.email,
            subject=f'Takeover request: {reminder.title}',
            message=plain_body,
            html_content=html_body,
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
    summary='Accept a reassignment request',
)
async def accept_reassignment_request(
    request_id: uuid.UUID,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> dict:
    """Accept via the in-app UI."""
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
    await _do_accept(repos, request_id, user.id)
    return await _enrich(repos, request_id)


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
    """Reject via the in-app UI."""
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
    await _do_reject(repos, request_id, user.id)
    return await _enrich(repos, request_id)
