"""Celery tasks for background job processing.

This module contains all Celery tasks including scheduled notifications.
Uses transaction_context pattern consistent with FastAPI endpoints.
"""

import asyncio
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import structlog
from sqlalchemy import select

from app.celery_app import celery_app
from app.db.async_pgsql_pool import AsyncPostgresPool
from app.db.transaction_context import transaction_context
from app.entities import NotificationEntity, ReminderEntity, UserEntity
from app.models import NotificationRecipients
from app.repos import RepoFactory
from app.services.notifications_service import NotificationService

logger = structlog.getLogger(__name__)


class CeleryPoolHolder:
    """Holds singleton database pool for Celery tasks."""

    _pool: AsyncPostgresPool | None = None

    @classmethod
    def get_pool(cls) -> AsyncPostgresPool:
        """Get or create singleton database pool."""
        if cls._pool is None:
            cls._pool = AsyncPostgresPool()
            logger.info('Database pool initialized for Celery tasks')
        return cls._pool


@asynccontextmanager
async def get_celery_tx_repo() -> AsyncGenerator[RepoFactory, None]:
    """Get repository with transaction for Celery tasks.

    Celery equivalent of get_shared_tx_repo from dependencies.py.
    Uses transaction_context for automatic commit/rollback.
    """
    pool = CeleryPoolHolder.get_pool()
    async with transaction_context(pool) as session:
        yield RepoFactory(pgsql_session=session)


@celery_app.task(name='app.tasks.send_scheduled_notifications')
def send_scheduled_notifications() -> dict:
    """Periodic task to send scheduled notifications.

    This task runs every minute via Celery Beat and checks for notifications
    that are due to be sent (scheduled_time <= now and sent_at is NULL).
    """
    logger.info('Starting scheduled notifications check')

    # Run async function in sync context
    result = asyncio.run(_send_scheduled_notifications_async())

    logger.info(
        'Scheduled notifications check completed',
        sent_count=result['sent'],
        failed_count=result['failed'],
    )

    return result


async def _send_scheduled_notifications_async() -> dict:
    """Async implementation of scheduled notification sending.

    Uses transaction_context for automatic commit/rollback.
    Processes each notification in its own transaction to avoid connection issues.
    """
    sent_count = 0
    failed_count = 0

    # First, get the list of due notifications
    async with get_celery_tx_repo() as repos:
        due_notifications = await _get_due_notifications(repos)
        logger.info(f'Found {len(due_notifications)} notifications due for sending')

    # Process each notification in its own transaction
    for notification in due_notifications:
        try:
            async with get_celery_tx_repo() as repos:
                notification_service = NotificationService(repos=repos)

                # Fetch user and reminder details
                user = await repos.user_pgsql_repo.find_by_id(notification.user_id)
                reminder = await repos.reminder_pgsql_repo.find_by_id(notification.reminder_id)

                if user is None:
                    logger.error(f'User not found for notification {notification.id}')
                    failed_count += 1
                    continue

                if reminder is None:
                    logger.error(f'Reminder not found for notification {notification.id}')
                    failed_count += 1
                    continue

                # Send the notification
                success = notification_service.send_reminder_notification(
                    user=user,
                    reminder=reminder,
                    notification=notification,
                )

                if success:
                    # Mark as sent
                    await notification_service.mark_notification_as_sent(notification)
                    sent_count += 1
                    logger.info(f'Successfully sent scheduled notification {notification.id} to user {user.email}')
                else:
                    failed_count += 1
                    logger.error(f'Failed to send scheduled notification {notification.id} to user {user.email}')

        except Exception as e:
            failed_count += 1
            # Use exception logging to include traceback
            logger.exception(f'Error processing notification {notification.id}: {e}')

    return {'sent': sent_count, 'failed': failed_count}


async def _get_due_notifications(repos: RepoFactory) -> list[NotificationEntity]:
    """Get all notifications that are due to be sent.

    Retrieves notifications where:
    - scheduled_time <= current time
    - sent_at is NULL

    Args:
        repos: Repository factory

    Returns:
        List of notification entities that need to be sent
    """
    now = datetime.now(timezone.utc)

    # Query for due notifications
    query = (
        select(NotificationRecipients)
        .where(
            NotificationRecipients.scheduled_time <= now,
            NotificationRecipients.sent_at.is_(None),
        )
        .order_by(NotificationRecipients.scheduled_time.asc())
    )

    result = await repos.pgsql_session.execute(query)
    instances = result.scalars().all()

    notifications = [NotificationEntity.model_validate(instance) for instance in instances]

    logger.info(f'Found {len(notifications)} due notifications')

    return notifications


@celery_app.task(name='app.tasks.send_immediate_notification')
def send_immediate_notification(
    user_id: str,
    reminder_id: str,
    notification_id: str,
) -> dict:
    """Task to send an immediate notification (optional async alternative).

    This task can be called directly to send a notification asynchronously
    via Celery instead of sending it synchronously in the request handler.

    Args:
        user_id: UUID of the user to notify
        reminder_id: UUID of the reminder
        notification_id: UUID of the notification

    Returns:
        Dict with success status
    """
    logger.info(f'Sending immediate notification {notification_id} for reminder {reminder_id} to user {user_id}')

    result = asyncio.run(_send_immediate_notification_async(user_id, reminder_id, notification_id))

    return result


async def _send_immediate_notification_async(
    user_id: str,
    reminder_id: str,
    notification_id: str,
) -> dict:
    """Async implementation of immediate notification sending.

    Uses transaction_context for automatic commit/rollback.
    """
    async with get_celery_tx_repo() as repos:
        notification_service = NotificationService(repos=repos)

        # Fetch entities
        user = await repos.user_pgsql_repo.find_by_id(uuid.UUID(user_id))
        reminder = await repos.reminder_pgsql_repo.find_by_id(uuid.UUID(reminder_id))
        notification = await repos.notification_pgsql_repo.find_by_id(uuid.UUID(notification_id))

        if not all([user, reminder, notification]):
            logger.error('One or more entities not found')
            return {'success': False, 'error': 'Entity not found'}

        # Send notification
        # Narrow types for mypy: cast values to concrete types now that we've
        # returned earlier if any were missing.
        from typing import cast

        user = cast(UserEntity, user)
        reminder = cast(ReminderEntity, reminder)
        notification = cast(NotificationEntity, notification)
        success = notification_service.send_reminder_notification(
            user=user,
            reminder=reminder,
            notification=notification,
        )

        if success:
            # Mark as sent
            await notification_service.mark_notification_as_sent(notification)
            logger.info(f'Immediate notification {notification_id} sent successfully')
            return {'success': True}
        else:
            logger.error(f'Failed to send immediate notification {notification_id}')
            return {'success': False, 'error': 'Send failed'}

        # transaction_context handles commit automatically


__all__ = [
    'send_immediate_notification',
    'send_scheduled_notifications',
]
