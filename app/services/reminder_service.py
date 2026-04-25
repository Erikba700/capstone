import uuid

import structlog

from app.entities import NotificationEntity, UserEntity
from app.entities.reminder import ReminderEntity
from app.exceptions import BadRequestError
from app.repos import RepoFactory
from app.schemas.reminder_schemas import (
    RemindersCreateRequestSchema,
    RemindersFiltersSchema,
    RemindersUpdateRequestSchema,
)
from app.services.notifications_service import NotificationService

logger = structlog.getLogger(__name__)


class ReminderService:
    """Reminder use cases."""

    def __init__(
        self,
        repos: RepoFactory,
    ) -> None:
        self.repos = repos

    async def create_reminder(
        self,
        entity: ReminderEntity,
        schema: RemindersCreateRequestSchema,
    ) -> ReminderEntity:
        """Create a new reminder.

        Validates that owner exists before insertion because owner_id is a FK
        to users table. If user_id is provided, validates that user exists and
        sends notification immediately if scheduled_time is None.
        """
        owner_id = uuid.UUID(str(entity.owner_id))

        owner = await self.repos.user_pgsql_repo.find_by_id(owner_id)
        if owner is None:
            msg = 'Owner not found'
            raise BadRequestError(msg) from None

        reminder = await self.repos.reminder_pgsql_repo.insert(entity=entity)

        payload = schema.model_dump(exclude_unset=True)
        notification_service = NotificationService(repos=self.repos)

        # Handle notification if user_id is provided
        if 'user_id' in payload and 'scheduled_time' in payload:
            notification_user = await self.repos.user_pgsql_repo.find_by_id(payload['user_id'])
            if notification_user is None:
                msg = f'User with id {schema.user_id} not found'
                raise BadRequestError(msg) from None

            notification = NotificationEntity.create_new(
                user_id=notification_user.id,
                reminder_id=reminder.id,
                message=f'New reminder created: {reminder.title}',
                creator_email=owner.email,
                scheduled_time=schema.scheduled_time,
            )

            created_notification = await self.repos.notification_pgsql_repo.insert(notification)

            notification_scheduled_time = payload.pop('scheduled_time', None)

            if notification_scheduled_time is None:
                success = notification_service.send_reminder_notification(
                    user=notification_user,
                    reminder=reminder,
                    notification=notification,
                )
                if success:
                    logger.info(
                        f'Immediate notification sent to user {notification_user.email} for reminder {reminder.title}'
                    )
                    # Mark as sent
                    await notification_service.mark_notification_as_sent(created_notification)
                else:
                    logger.error(
                        f'Failed to send immediate notification to user '
                        f'{notification_user.id} for reminder {reminder.id}'
                    )
            else:
                # scheduled_time is provided, create scheduled notification in DB
                await notification_service.create_scheduled_notification(notification)
                logger.info(
                    f'Scheduled notification created for user {notification_user.email} at {schema.scheduled_time}'
                )

        return reminder

    async def get_reminders_by_owner_id(
        self,
        owner_id: uuid.UUID,
        filters: RemindersFiltersSchema,
    ) -> list[ReminderEntity]:
        """Fetch reminders by owner id."""
        reminders_dict = filters.model_dump(exclude_none=True)
        reminders = await self.repos.reminder_pgsql_repo.fetch_reminders_by_owner_id(
            owner_id=owner_id,
            filters=reminders_dict,
        )
        return reminders

    async def update_reminder(
        self,
        schema: RemindersUpdateRequestSchema,
        reminder_id: uuid.UUID,
        user: UserEntity,
    ) -> ReminderEntity:
        """Update a reminder.

        If user_id is provided, validates that user exists and sends
        notification immediately if scheduled_time is None.
        """
        reminder = await self.repos.reminder_pgsql_repo.find_by_id(reminder_id=reminder_id)
        if reminder is None:
            msg = 'Reminder not found'
            raise BadRequestError(msg) from None

        # Convert schema to dict with only fields that were actually set
        payload = schema.model_dump(exclude_unset=True)

        # Handle notification if user_id is provided in the update
        if 'user_id' in payload and payload['user_id'] is not None:
            notification_user = await self.repos.user_pgsql_repo.find_by_id(payload['user_id'])
            if notification_user is None:
                msg = f'User with id {payload["user_id"]} not found'
                raise BadRequestError(msg) from None

            # Remove user_id and scheduled_time from payload as they're not reminder fields
            notification_user_id = payload.pop('user_id')
            notification_scheduled_time = payload.pop('scheduled_time', None)

            # Update the reminder with remaining fields
            updated_reminder = reminder.update(
                payload=payload,
                user=user,
            )
            updated_reminder = await self.repos.reminder_pgsql_repo.update(entity=updated_reminder)

            # Get the reminder owner for the creator_email

            # Create notification entity with creator's email
            notification = NotificationEntity.create_new(
                user_id=notification_user_id,
                reminder_id=updated_reminder.id,
                message=f'Reminder updated: {updated_reminder.title}',
                creator_email=user.email,
                scheduled_time=notification_scheduled_time,
            )

            notification_service = NotificationService(repos=self.repos)

            # If scheduled_time is None, send notification immediately
            if notification_scheduled_time is None:
                # Create notification in DB and send immediately
                (
                    created_notification,
                    success,
                ) = await notification_service.send_and_create_notification(
                    user=notification_user,
                    reminder=updated_reminder,
                    notification=notification,
                )
                if success:
                    logger.info(
                        f'Immediate notification sent to user {notification_user.id} '
                        f'for updated reminder {updated_reminder.id}'
                    )
                    # Mark as sent
                    await notification_service.mark_notification_as_sent(created_notification)
                else:
                    logger.error(
                        f'Failed to send immediate notification to user '
                        f'{notification_user.id} for updated reminder {updated_reminder.id}'
                    )
            else:
                # scheduled_time is provided, create scheduled notification in DB
                await notification_service.create_scheduled_notification(notification)
                logger.info(
                    f'Scheduled notification created for user {notification_user.id} at {notification_scheduled_time}'
                )

            return updated_reminder
        else:
            # No user_id provided, just update the reminder normally
            # Remove scheduled_time if present (not a reminder field)
            payload.pop('scheduled_time', None)
            payload.pop('user_id', None)

            updated_reminder = reminder.update(
                payload=payload,
                user=user,
            )
            updated_reminder = await self.repos.reminder_pgsql_repo.update(entity=updated_reminder)
            return updated_reminder

    async def delete_reminder_by_id(self, reminder_id: uuid.UUID) -> None:
        """Delete a reminder by id."""
        reminder = await self.repos.reminder_pgsql_repo.find_by_id(reminder_id=reminder_id)
        if reminder is None:
            msg = 'Reminder not found'
            raise BadRequestError(msg) from None
        await self.repos.reminder_pgsql_repo.delete_by_id(reminder_id=reminder.id)

    async def enrich_reminder_with_notification_info(self, reminder: ReminderEntity) -> dict:
        """Enrich reminder with notification scheduling information.

        Returns a dict with reminder data plus scheduling info.
        """
        reminder_dict = reminder.model_dump()

        # Get latest notification for this reminder
        notifications = await self.repos.notification_pgsql_repo.fetch_notifications_by_reminder_id(
            reminder_id=reminder.id
        )

        if notifications:
            # Get the most recent notification
            latest_notification = notifications[0]
            reminder_dict['scheduled_time'] = latest_notification.scheduled_time
            reminder_dict['notified_immediately'] = (
                latest_notification.sent_at is not None and latest_notification.scheduled_time is None
            )
        else:
            reminder_dict['scheduled_time'] = None
            reminder_dict['notified_immediately'] = False

        return reminder_dict

    async def enrich_reminders_with_notification_info(self, reminders: list[ReminderEntity]) -> list[dict]:
        """Enrich multiple reminders with notification scheduling information."""
        enriched_reminders = []
        for reminder in reminders:
            enriched = await self.enrich_reminder_with_notification_info(reminder)
            enriched_reminders.append(enriched)
        return enriched_reminders
