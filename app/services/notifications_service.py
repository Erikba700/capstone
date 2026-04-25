import uuid
from typing import Any

import structlog

from app.config import settings
from app.entities import NotificationEntity, ReminderEntity, UserEntity
from app.repos import RepoFactory
from app.services.notification_providers import (
    EmailNotificationProvider,
    NotificationProvider,
)
from app.utils import get_utc_now

logger = structlog.getLogger(__name__)


class NotificationService:
    """Service for managing and sending notifications."""

    def __init__(
        self,
        repos: RepoFactory,
        notification_provider: NotificationProvider | None = None,
    ) -> None:
        """Initialize the notification service."""
        self.repos = repos

        if notification_provider is None:
            self.provider: NotificationProvider = EmailNotificationProvider(
                sender_email=settings.email_address,
                sender_password=settings.email_password,
            )
        else:
            self.provider = notification_provider

    def send_reminder_notification(
        self,
        user: UserEntity,
        reminder: ReminderEntity,
        notification: NotificationEntity,
        **kwargs: Any,
    ) -> bool:
        """Send a reminder notification to a user.

        Args:
            user: User to notify
            reminder: Reminder that triggered the notification
            notification: Notification entity with details
            **kwargs: Additional provider-specific parameters

        Returns:
            True if notification was sent successfully, False otherwise
        """
        # Format the notification message
        subject = self._format_subject(reminder)
        message = self._format_message(user, reminder, notification)

        # Send via the configured provider
        success = self.provider.send(
            recipient=user.email,
            subject=subject,
            message=message,
            **kwargs,
        )

        if success:
            logger.info(f'Reminder notification sent to user {user.email} for reminder {reminder.title}')
        else:
            logger.error(f'Failed to send reminder notification to user {user.email} for reminder {reminder.title}')

        return success

    def send_custom_notification(
        self,
        recipient: str,
        subject: str,
        message: str,
        **kwargs: Any,
    ) -> bool:
        """Send a custom notification with arbitrary content.

        Args:
            recipient: Recipient address (email, phone, etc.)
            subject: Notification subject
            message: Notification message
            **kwargs: Additional provider-specific parameters

        Returns:
            True if notification was sent successfully, False otherwise
        """
        success = self.provider.send(
            recipient=recipient,
            subject=subject,
            message=message,
            **kwargs,
        )

        if success:
            logger.info(f'Custom notification sent to {recipient}')
        else:
            logger.error(f'Failed to send custom notification to {recipient}')

        return success

    def send_bulk_notifications(
        self,
        users: list[UserEntity],
        subject: str,
        message: str,
        **kwargs: Any,
    ) -> dict[uuid.UUID, bool]:
        """Send the same notification to multiple users.

        Args:
            users: List of users to notify
            subject: Notification subject
            message: Notification message
            **kwargs: Additional provider-specific parameters

        Returns:
            Dictionary mapping user IDs to success status (True/False)
        """
        results = {}

        for user in users:
            success = self.provider.send(
                recipient=user.email,
                subject=subject,
                message=message,
                **kwargs,
            )
            results[user.id] = success

        successful_count = sum(results.values())
        logger.info(f'Bulk notification: {successful_count}/{len(users)} notifications sent successfully')

        return results

    def _format_subject(self, reminder: ReminderEntity) -> str:
        """Format the notification subject for a reminder.

        Args:
            reminder: Reminder entity

        Returns:
            Formatted subject string
        """
        return f'Reminder: {reminder.title}'

    def _format_message(
        self,
        user: UserEntity,
        reminder: ReminderEntity,
        notification: NotificationEntity,
    ) -> str:
        """Format the notification message for a reminder.

        Args:
            user: User receiving the notification
            reminder: Reminder entity
            notification: Notification entity

        Returns:
            Formatted message string
        """
        lines = [
            f'Hello {user.name},',
            '',
            f'This is a reminder about: {reminder.title}',
        ]

        if reminder.description:
            lines.extend(['', f'Details: {reminder.description}'])

        if notification.creator_email:
            lines.extend(['', f'Created by: {notification.creator_email}'])

        if notification.scheduled_time:
            lines.extend(
                [
                    '',
                    f'Scheduled for: {notification.scheduled_time.strftime("%Y-%m-%d %H:%M %Z")}',
                ]
            )

        if notification.message:
            lines.extend(['', f'Note: {notification.message}'])

        lines.extend(
            [
                '',
                'Best regards,',
                'Reminder Management System',
            ]
        )

        return '\n'.join(lines)

    async def create_notification(
        self,
        notification: NotificationEntity,
    ) -> NotificationEntity:
        """Create and persist a notification to the database.

        Args:
            notification: Notification entity to create

        Returns:
            Created notification entity with database-generated values
        """
        created_notification = await self.repos.notification_pgsql_repo.insert(entity=notification)
        logger.info(f'Notification created in database with id {created_notification.id}')
        return created_notification

    async def send_and_create_notification(
        self,
        user: UserEntity,
        reminder: ReminderEntity,
        notification: NotificationEntity,
        **kwargs: Any,
    ) -> tuple[NotificationEntity, bool]:
        """Create a notification in the database and send it immediately.

        This method first persists the notification to the database, then
        attempts to send it via the configured provider.

        Args:
            user: User to notify
            reminder: Reminder that triggered the notification
            notification: Notification entity with details
            **kwargs: Additional provider-specific parameters

        Returns:
            Tuple of (created_notification, send_success)
        """
        # First, persist to database
        created_notification = await self.create_notification(notification)

        # Then attempt to send
        success = self.send_reminder_notification(
            user=user,
            reminder=reminder,
            notification=created_notification,
            **kwargs,
        )

        return created_notification, success

    async def create_scheduled_notification(
        self,
        notification: NotificationEntity,
    ) -> NotificationEntity:
        """Create a scheduled notification in the database.

        This notification will be processed later by a background job
        (Celery/Redis) when its scheduled_time arrives.

        Args:
            notification: Notification entity with scheduled_time set

        Returns:
            Created notification entity
        """
        if notification.scheduled_time is None:
            msg = 'scheduled_time must be set for scheduled notifications'
            raise ValueError(msg)

        created_notification = await self.create_notification(notification)
        logger.info(f'Scheduled notification created for {notification.scheduled_time}')
        return created_notification

    async def mark_notification_as_sent(
        self,
        notification: NotificationEntity,
    ) -> NotificationEntity:
        """Mark a notification as sent by updating its sent_at timestamp.

        Args:
            notification: Notification entity to update

        Returns:
            Updated notification entity
        """
        updated_notification = notification.update({'sent_at': get_utc_now()})
        updated_notification = await self.repos.notification_pgsql_repo.update(entity=updated_notification)
        logger.info(f'Notification {notification.id} marked as sent')
        return updated_notification

    async def mark_notification_as_read(
        self,
        notification: NotificationEntity,
    ) -> NotificationEntity:
        """Mark a notification as read.

        Args:
            notification: Notification entity to update

        Returns:
            Updated notification entity
        """
        updated_notification = notification.update({'is_read': True})
        updated_notification = await self.repos.notification_pgsql_repo.update(entity=updated_notification)
        logger.info(f'Notification {notification.id} marked as read')
        return updated_notification

    def change_provider(self, provider: NotificationProvider) -> None:
        """Change the notification provider.

        This allows switching between different notification channels
        (email, SMS, Telegram, etc.) at runtime.

        Args:
            provider: New notification provider to use
        """
        self.provider = provider
        logger.info(f'Notification provider changed to {provider.__class__.__name__}')


# Convenience factory function
def create_notification_service(
    repos: RepoFactory,
    provider_type: str = 'email',
) -> NotificationService:
    """Factory function to create a NotificationService with a specific provider.

    Args:
        repos: Repository factory for database access
        provider_type: Type of provider to use ('email', 'sms', 'telegram')

    Returns:
        Configured NotificationService instance

    Raises:
        ValueError: If provider_type is not supported
    """
    if provider_type == 'email':
        provider = EmailNotificationProvider(
            sender_email=settings.email_address,
            sender_password=settings.email_password,
        )
    else:
        msg = f'Unsupported provider type: {provider_type}'
        raise ValueError(msg)

    return NotificationService(repos=repos, notification_provider=provider)
