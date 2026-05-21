import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user, get_shared_tx_repo
from app.entities import UserEntity
from app.exceptions import NotFoundError
from app.repos import RepoFactory
from app.schemas.base_schemas import BaseSchema

router = APIRouter(tags=['Notifications'])


class NotificationResponseSchema(BaseSchema):
    """Schema for a single notification history item."""

    id: uuid.UUID
    reminder_id: uuid.UUID | None
    message: str | None
    creator_email: str | None
    scheduled_time: str | None
    sent_at: str | None
    is_read_at: str | None
    created_at: str


@router.get('/notifications', response_model=list[NotificationResponseSchema])
async def list_notifications(
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> list[dict]:
    """Return all notifications for the authenticated user, newest first."""
    notifications = await repos.notification_pgsql_repo.fetch_notifications_by_user_id(
        user_id=user.id,
    )
    return [
        {
            'id': n.id,
            'reminder_id': n.reminder_id,
            'message': n.message,
            'creator_email': n.creator_email,
            'scheduled_time': n.scheduled_time.isoformat() if n.scheduled_time else None,
            'sent_at': n.sent_at.isoformat() if n.sent_at else None,
            'is_read_at': n.is_read_at.isoformat() if n.is_read_at else None,
            'created_at': n.created_at.isoformat(),
        }
        for n in notifications
    ]


@router.patch('/notifications/{notification_id}/read', response_model=NotificationResponseSchema)
async def mark_notification_read(
    notification_id: uuid.UUID,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> dict:
    """Mark a single notification as read."""
    from app.entities.domain_entity import DomainEntity

    notification = await repos.notification_pgsql_repo.find_by_id(notification_id)
    if notification is None or notification.user_id != user.id:
        msg = 'Notification not found'
        raise NotFoundError(msg)

    if notification.is_read_at is None:
        now = DomainEntity.generate_current_timestamp()
        updated = notification.update({'is_read_at': now})
        notification = await repos.notification_pgsql_repo.update(updated)

    return {
        'id': notification.id,
        'reminder_id': notification.reminder_id,
        'message': notification.message,
        'creator_email': notification.creator_email,
        'scheduled_time': notification.scheduled_time.isoformat() if notification.scheduled_time else None,
        'sent_at': notification.sent_at.isoformat() if notification.sent_at else None,
        'is_read_at': notification.is_read_at.isoformat() if notification.is_read_at else None,
        'created_at': notification.created_at.isoformat(),
    }


@router.patch('/notifications/read-all')
async def mark_all_notifications_read(
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> dict:
    """Mark all unread notifications as read for the authenticated user."""
    from app.entities.domain_entity import DomainEntity

    notifications = await repos.notification_pgsql_repo.fetch_notifications_by_user_id(
        user_id=user.id,
    )
    now = DomainEntity.generate_current_timestamp()
    count = 0
    for n in notifications:
        if n.is_read_at is None:
            updated = n.update({'is_read_at': now})
            await repos.notification_pgsql_repo.update(updated)
            count += 1

    return {'marked_read': count}
