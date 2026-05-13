import uuid

import structlog

from app.entities import NotificationEntity, UserEntity
from app.entities.friendship import FriendshipStatus
from app.entities.reminder import ReminderEntity
from app.entities.reminder_assignee import ReminderAssigneeEntity
from app.exceptions import BadRequestError
from app.repos import RepoFactory
from app.schemas.reminder_schemas import (
    RemindersCreateRequestSchema,
    RemindersFiltersSchema,
    RemindersUpdateRequestSchema,
)
from app.services.notifications_service import NotificationService
from app.utils import convert_to_utc

logger = structlog.getLogger(__name__)


class ReminderService:
    """Reminder use cases."""

    def __init__(
        self,
        repos: RepoFactory,
    ) -> None:
        self.repos = repos

    async def _handle_create_notification(
        self,
        schema: RemindersCreateRequestSchema,
        reminder: ReminderEntity,
        owner: UserEntity,
    ) -> None:
        """Send or schedule a notification when creating a reminder."""
        payload = schema.model_dump(exclude_unset=True)
        if 'user_id' not in payload or 'scheduled_time' not in payload:
            return

        notification_user = await self.repos.user_pgsql_repo.find_by_id(payload['user_id'])
        if notification_user is None:
            msg = f'User with id {schema.user_id} not found'
            raise BadRequestError(msg) from None

        scheduled_time_utc = None
        if schema.scheduled_time is not None:
            scheduled_time_utc = convert_to_utc(schema.scheduled_time, notification_user.timezone)
            logger.info(
                'Converted scheduled time to UTC',
                original_time=schema.scheduled_time,
                utc_time=scheduled_time_utc,
                user_timezone=notification_user.timezone,
            )

        notification = NotificationEntity.create_new(
            user_id=notification_user.id,
            reminder_id=reminder.id,
            message=f'New reminder created: {reminder.title}',
            creator_email=owner.email,
            scheduled_time=scheduled_time_utc,
        )

        notification_service = NotificationService(repos=self.repos)
        notification_scheduled_time = payload.get('scheduled_time')

        if notification_scheduled_time is None:
            created_notification = await self.repos.notification_pgsql_repo.insert(notification)
            success = notification_service.send_reminder_notification(
                user=notification_user,
                reminder=reminder,
                notification=created_notification,
            )
            if success:
                logger.info('Immediate notification sent', user=notification_user.email, reminder=reminder.title)
                await notification_service.mark_notification_as_sent(created_notification)
            else:
                logger.error('Failed to send immediate notification', user=notification_user.id, reminder=reminder.id)
        else:
            await notification_service.create_scheduled_notification(notification)
            logger.info(
                'Scheduled notification created',
                user=notification_user.email,
                utc_time=scheduled_time_utc,
                user_timezone=notification_user.timezone,
            )

    async def _handle_assignee(
        self,
        assignee_id: uuid.UUID,
        reminder: ReminderEntity,
        entity: ReminderEntity,
        schema: RemindersCreateRequestSchema,
        owner: 'UserEntity',
    ) -> None:
        """Validate and create a single reminder assignee, optionally notifying them."""
        if assignee_id != reminder.owner_id:
            if entity.group_id is not None:
                in_group = await self.repos.group_member_pgsql_repo.find_by_group_and_user(
                    group_id=entity.group_id,
                    user_id=assignee_id,
                )
                if in_group is None:
                    msg = f'User {assignee_id} is not a member of the group'
                    raise BadRequestError(msg)
            else:
                friendship = await self.repos.friendship_pgsql_repo.find_between_users(reminder.owner_id, assignee_id)
                if friendship is None or friendship.status != FriendshipStatus.ACCEPTED:
                    msg = f'User {assignee_id} is not your friend'
                    raise BadRequestError(msg)

        assignee_entity = ReminderAssigneeEntity.create_new(
            reminder_id=reminder.id,
            user_id=assignee_id,
            assigned_by=reminder.owner_id,
        )
        await self.repos.reminder_assignee_pgsql_repo.insert(entity=assignee_entity)
        logger.info('Created reminder assignee', user_id=assignee_id, reminder_id=reminder.id)

        if assignee_id != reminder.owner_id and schema.notify_assignees:
            assignee_user = await self.repos.user_pgsql_repo.find_by_id(assignee_id)
            if assignee_user is not None:
                notification_service = NotificationService(repos=self.repos)
                from app.entities import NotificationEntity

                # Convert assignee scheduled time to their timezone UTC
                scheduled_time_utc = None
                if schema.assignee_scheduled_time is not None:
                    scheduled_time_utc = convert_to_utc(
                        schema.assignee_scheduled_time,
                        assignee_user.timezone,
                    )
                    logger.info(
                        'Converted assignee scheduled time to UTC',
                        original_time=schema.assignee_scheduled_time,
                        utc_time=scheduled_time_utc,
                        user_timezone=assignee_user.timezone,
                    )

                notif = NotificationEntity.create_new(
                    user_id=assignee_id,
                    reminder_id=reminder.id,
                    message=f'You were assigned a reminder: {reminder.title}',
                    creator_email=owner.email,
                    scheduled_time=scheduled_time_utc,
                )

                if scheduled_time_utc is not None:
                    await notification_service.create_scheduled_notification(notif)
                    logger.info(
                        'Scheduled assignee notification',
                        user=assignee_user.email,
                        utc_time=scheduled_time_utc,
                    )
                else:
                    created_notif = await self.repos.notification_pgsql_repo.insert(notif)
                    success = notification_service.send_reminder_notification(
                        user=assignee_user,
                        reminder=reminder,
                        notification=created_notif,
                    )
                    if success:
                        await notification_service.mark_notification_as_sent(created_notif)

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

        # Validate group membership if group_id is provided
        if entity.group_id is not None:
            membership = await self.repos.group_member_pgsql_repo.find_by_group_and_user(
                group_id=entity.group_id,
                user_id=owner_id,
            )
            if membership is None:
                msg = 'You are not a member of this group'
                raise BadRequestError(msg) from None

        reminder = await self.repos.reminder_pgsql_repo.insert(entity=entity)

        await self._handle_create_notification(schema=schema, reminder=reminder, owner=owner)

        if schema.assignee_ids:
            for assignee_id in schema.assignee_ids:
                await self._handle_assignee(
                    assignee_id=assignee_id,
                    reminder=reminder,
                    entity=entity,
                    schema=schema,
                    owner=owner,
                )

        return reminder

    async def list_group_reminders(self, group_id: uuid.UUID) -> list[ReminderEntity]:
        """Fetch all reminders belonging to a group."""
        return await self.repos.reminder_pgsql_repo.fetch_reminders_by_group_id(group_id=group_id)

    async def get_reminders_by_owner_id(
        self,
        owner_id: uuid.UUID,
        filters: RemindersFiltersSchema,
    ) -> list[ReminderEntity]:
        """Fetch reminders by owner id, optionally including assigned reminders."""
        status_filters: dict = {}
        if filters.status is not None:
            status_filters['status'] = filters.status

        owned = await self.repos.reminder_pgsql_repo.fetch_reminders_by_owner_id(
            owner_id=owner_id,
            filters=status_filters,
        )

        if not filters.include_assigned:
            return owned

        assigned = await self.repos.reminder_pgsql_repo.fetch_reminders_assigned_to_user(
            user_id=owner_id,
        )

        # Merge deduped by id, owned first
        seen: set[uuid.UUID] = {r.id for r in owned}
        merged = list(owned)
        for r in assigned:
            if r.id not in seen and (filters.status is None or r.status == filters.status):
                seen.add(r.id)
                merged.append(r)

        return merged

    async def update_reminder(
        self,
        schema: RemindersUpdateRequestSchema,
        reminder_id: uuid.UUID,
        user: UserEntity,
    ) -> ReminderEntity:
        """Update a reminder.

        If user_id is provided, validates that user exists and sends
        notification immediately if scheduled_time is None.
        Assignees (non-owners) may only update the status field.
        """
        reminder = await self.repos.reminder_pgsql_repo.find_by_id(reminder_id=reminder_id)
        if reminder is None:
            msg = 'Reminder not found'
            raise BadRequestError(msg) from None

        # If caller is not the owner, verify they're an assignee and restrict to status-only
        from app.exceptions import AuthorizationError

        if reminder.owner_id != user.id:
            assignment = await self.repos.reminder_assignee_pgsql_repo.find_by_reminder_and_user(
                reminder_id=reminder_id,
                user_id=user.id,
            )
            if assignment is None:
                msg = 'You are not authorized to update this reminder'
                raise AuthorizationError(msg)
            # Assignees may only change status
            payload = schema.model_dump(exclude_unset=True)
            allowed = {'status'}
            disallowed = set(payload.keys()) - allowed
            if disallowed:
                msg = f'Assignees may only update the status field (got: {disallowed})'
                raise AuthorizationError(msg)
            updated_reminder = reminder.update(payload=payload, user=user)
            return await self.repos.reminder_pgsql_repo.update(entity=updated_reminder)

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

            # Convert scheduled_time from user's timezone to UTC if provided
            scheduled_time_utc = None
            if notification_scheduled_time is not None:
                scheduled_time_utc = convert_to_utc(
                    notification_scheduled_time,
                    notification_user.timezone,
                )
                logger.info(
                    f'Converted scheduled time from {notification_user.timezone} to UTC',
                    original_time=notification_scheduled_time,
                    utc_time=scheduled_time_utc,
                    user_timezone=notification_user.timezone,
                )

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
                scheduled_time=scheduled_time_utc,
            )

            notification_service = NotificationService(repos=self.repos)

            # If scheduled_time is None, send notification immediately
            if scheduled_time_utc is None:
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
                    f'Scheduled notification created for user {notification_user.id} at '
                    f'{scheduled_time_utc} UTC (user timezone: {notification_user.timezone})'
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
            latest_notification = notifications[0]
            reminder_dict['scheduled_time'] = latest_notification.scheduled_time
            reminder_dict['notified_immediately'] = (
                latest_notification.sent_at is not None and latest_notification.scheduled_time is None
            )
        else:
            reminder_dict['scheduled_time'] = None
            reminder_dict['notified_immediately'] = False

        # Attach assignee user ids
        assignees = await self.repos.reminder_assignee_pgsql_repo.list_by_reminder_id(reminder_id=reminder.id)
        reminder_dict['assignees'] = [str(a.user_id) for a in assignees]

        # Build rich assignee details
        assignee_details = []
        for a in assignees:
            assignee_user = await self.repos.user_pgsql_repo.find_by_id(a.user_id)
            assigner_user = await self.repos.user_pgsql_repo.find_by_id(a.assigned_by)
            assignee_details.append(
                {
                    'id': str(a.id),
                    'user_id': str(a.user_id),
                    'user_name': assignee_user.name if assignee_user else None,
                    'user_email': assignee_user.email if assignee_user else None,
                    'assigned_by': str(a.assigned_by),
                    'assigned_by_name': assigner_user.name if assigner_user else None,
                    'assigned_at': a.assigned_at,
                    'completed_at': a.completed_at,
                }
            )
        reminder_dict['assignee_details'] = assignee_details

        # Resolve updated_by name
        reminder_dict['updated_by_name'] = None
        if reminder.updated_by is not None:
            updater = await self.repos.user_pgsql_repo.find_by_id(reminder.updated_by)
            if updater is not None:
                reminder_dict['updated_by_name'] = updater.name

        return reminder_dict

    async def enrich_reminders_with_notification_info(self, reminders: list[ReminderEntity]) -> list[dict]:
        """Enrich multiple reminders with notification scheduling information."""
        enriched_reminders = []
        for reminder in reminders:
            enriched = await self.enrich_reminder_with_notification_info(reminder)
            enriched_reminders.append(enriched)
        return enriched_reminders
