import uuid
from datetime import datetime as dt

import structlog

from app.entities import NotificationEntity, UserEntity
from app.entities.friendship import FriendshipStatus
from app.entities.group_members import MemberRoles
from app.entities.reminder import ReminderEntity
from app.entities.reminder_assignee import ReminderAssigneeEntity
from app.exceptions import AuthorizationError, BadRequestError
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
        if 'user_id' not in payload or payload['user_id'] is None:
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
            success = await notification_service.send_reminder_notification(
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
    ) -> tuple[uuid.UUID, uuid.UUID, 'UserEntity | None', 'NotificationEntity | None'] | None:
        """Validate and create a single reminder assignee.

        Returns a tuple of (assignee_id, assignment_id, assignee_user, notif_entity)
        when an immediate notification should be sent, so callers can fire them
        concurrently. Returns None when no email needs to be sent (scheduled or
        owner self-assignment).
        """
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
        created_assignment = await self.repos.reminder_assignee_pgsql_repo.insert(entity=assignee_entity)
        logger.info('Created reminder assignee', user_id=assignee_id, reminder_id=reminder.id)

        if assignee_id == reminder.owner_id or not schema.notify_assignees:
            return None

        assignee_user = await self.repos.user_pgsql_repo.find_by_id(assignee_id)
        if assignee_user is None:
            return None

        from app.entities import NotificationEntity as _NotifEntity

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

        notif = _NotifEntity.create_new(
            user_id=assignee_id,
            reminder_id=reminder.id,
            message=f'You were assigned a reminder: {reminder.title}',
            creator_email=owner.email,
            scheduled_time=scheduled_time_utc,
        )

        notification_service = NotificationService(repos=self.repos)

        if scheduled_time_utc is not None:
            await notification_service.create_scheduled_notification(notif)
            logger.info(
                'Scheduled assignee notification',
                user=assignee_user.email,
                utc_time=scheduled_time_utc,
            )
            return None

        # Immediate: persist notification row now, return info for concurrent send
        created_notif = await self.repos.notification_pgsql_repo.insert(notif)
        return (assignee_id, created_assignment.id, assignee_user, created_notif)

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
            await self._create_assignees_and_notify(schema=schema, reminder=reminder, entity=entity, owner=owner)

        return reminder

    async def _create_assignees_and_notify(
        self,
        schema: RemindersCreateRequestSchema,
        reminder: ReminderEntity,
        entity: ReminderEntity,
        owner: UserEntity,
    ) -> None:
        """Insert all assignee records then batch-send immediate notifications."""
        pending_sends = []
        for assignee_id in schema.assignee_ids or []:
            result = await self._handle_assignee(
                assignee_id=assignee_id,
                reminder=reminder,
                entity=entity,
                schema=schema,
                owner=owner,
            )
            if result is not None:
                pending_sends.append(result)

        logger.info('Collected pending assignee sends', count=len(pending_sends))
        if not pending_sends:
            return

        notification_service = NotificationService(repos=self.repos)
        valid = [(au, cn, aid) for (_, aid, au, cn) in pending_sends if au is not None and cn is not None]
        logger.info('Valid assignee sends after filter', count=len(valid))
        if valid:
            batch_results = await notification_service.send_reminder_notifications_batch(
                [(au, reminder, cn, aid) for (au, cn, aid) in valid]
            )
            for (au, cn, _), sent in zip(valid, batch_results, strict=True):
                if sent:
                    await notification_service.mark_notification_as_sent(cn)
                else:
                    logger.error('Failed to send assignee notification', user_id=au.id)

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

    async def _sync_assignees(
        self,
        reminder: ReminderEntity,
        new_ids: list[uuid.UUID],
        assigned_by: uuid.UUID,
        notify: bool = False,  # noqa: FBT001, FBT002
        scheduled_time: dt | None = None,
    ) -> None:
        """Replace existing assignees with new_ids, adding/removing as needed."""
        existing = await self.repos.reminder_assignee_pgsql_repo.list_by_reminder_id(
            reminder_id=reminder.id,
        )
        existing_ids = {e.user_id for e in existing}
        new_set = set(new_ids)

        # Remove assignees no longer in the list
        for assignment in existing:
            if assignment.user_id not in new_set:
                await self.repos.reminder_assignee_pgsql_repo.delete_by_id(
                    assignee_id=assignment.id,
                )

        # Add new assignees
        pending_sends = []
        for uid in new_set - existing_ids:
            entity = ReminderAssigneeEntity.create_new(
                reminder_id=reminder.id,
                user_id=uid,
                assigned_by=assigned_by,
            )
            created_assignment = await self.repos.reminder_assignee_pgsql_repo.insert(entity=entity)

            if notify:
                assignee_user = await self.repos.user_pgsql_repo.find_by_id(uid)
                assigner_user = await self.repos.user_pgsql_repo.find_by_id(assigned_by)
                if assignee_user is not None and assigner_user is not None:
                    notification = NotificationEntity.create_new(
                        user_id=uid,
                        reminder_id=reminder.id,
                        message=f'You were assigned to "{reminder.title}" by {assigner_user.name}',
                        creator_email=assigner_user.email,
                        scheduled_time=scheduled_time,
                    )
                    notification_service = NotificationService(repos=self.repos)
                    if scheduled_time is not None:
                        await notification_service.create_scheduled_notification(notification)
                    else:
                        created_notif = await self.repos.notification_pgsql_repo.insert(notification)
                        pending_sends.append(
                            (assignee_user, created_notif, created_assignment.id, notification_service)
                        )

        # Fire all immediate notifications over ONE SMTP connection via batch send
        if pending_sends:
            svc = NotificationService(repos=self.repos)
            batch_results = await svc.send_reminder_notifications_batch(
                [(u, reminder, n, aid) for (u, n, aid, _) in pending_sends]
            )
            for (_, n, _, _), sent in zip(pending_sends, batch_results, strict=True):
                if sent:
                    await svc.mark_notification_as_sent(n)

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

        # If caller is not the owner, delegate to a helper to reduce complexity

        if reminder.owner_id != user.id:
            return await self._handle_non_owner_update(
                reminder=reminder, schema=schema, reminder_id=reminder_id, user=user
            )

        # Convert schema to dict with only fields that were actually set
        payload = schema.model_dump(exclude_unset=True)

        # Extract assignee-related fields early
        new_assignee_ids: list[uuid.UUID] | None = payload.pop('assignee_ids', None)
        notify_new_assignees: bool = payload.pop('notify_assignees', False)
        assignee_scheduled_time = payload.pop('assignee_scheduled_time', None)

        if 'user_id' in payload and payload['user_id'] is not None:
            # Handle the special case where an immediate/scheduled notification to a user is requested
            return await self._process_update_with_notification_and_assignees(
                payload=payload,
                reminder=reminder,
                user=user,
                new_assignee_ids=new_assignee_ids,
                notify_new_assignees=notify_new_assignees,
                assignee_scheduled_time=assignee_scheduled_time,
            )

        # Normal update path (no explicit notification-to-user requested)
        payload.pop('scheduled_time', None)
        payload.pop('user_id', None)

        updated_reminder = reminder.update(payload=payload, user=user)
        updated_reminder = await self.repos.reminder_pgsql_repo.update(entity=updated_reminder)

        if new_assignee_ids is not None:
            await self._sync_assignees(
                reminder=updated_reminder,
                new_ids=new_assignee_ids,
                assigned_by=user.id,
                notify=notify_new_assignees,
                scheduled_time=assignee_scheduled_time,
            )
        return updated_reminder

    async def _handle_non_owner_update(
        self,
        reminder: ReminderEntity,
        schema: RemindersUpdateRequestSchema,
        reminder_id: uuid.UUID,
        user: UserEntity,
    ) -> ReminderEntity:
        """Handle update attempts from non-owners (assignees or group members).

        Returns the updated reminder or raises AuthorizationError.
        """
        from app.exceptions import AuthorizationError

        # If this is a group reminder, check membership/role
        if reminder.group_id is not None:
            from app.entities.group_members import MemberRoles

            membership = await self.repos.group_member_pgsql_repo.find_by_group_and_user(
                group_id=reminder.group_id,
                user_id=user.id,
            )
            if membership is None:
                msg = 'You are not a member of this group'
                raise AuthorizationError(msg)

            # Admins/owners can edit everything
            if membership.role in (MemberRoles.ADMIN, MemberRoles.OWNER):
                payload = schema.model_dump(exclude_unset=True)
                payload.pop('user_id', None)
                payload.pop('scheduled_time', None)
                updated_reminder = reminder.update(payload=payload, user=user)
                return await self.repos.reminder_pgsql_repo.update(entity=updated_reminder)

            # Non-privileged group members must be creator or assignee; if assignee, restrict to status
            assignment = await self.repos.reminder_assignee_pgsql_repo.find_by_reminder_and_user(
                reminder_id=reminder_id,
                user_id=user.id,
            )
            if assignment is None and reminder.owner_id != user.id:
                msg = 'You can only edit reminders you created or are assigned to'
                raise AuthorizationError(msg)

            payload = schema.model_dump(exclude_unset=True)
            allowed = {'status'}
            disallowed = set(payload.keys()) - allowed
            if disallowed:
                msg = f'Group assignees may only update status (got: {disallowed})'
                raise AuthorizationError(msg)

            payload.pop('user_id', None)
            payload.pop('scheduled_time', None)
            updated_reminder = reminder.update(payload=payload, user=user)
            return await self.repos.reminder_pgsql_repo.update(entity=updated_reminder)

        # Non-group reminder: require assignee and restrict to status
        assignment = await self.repos.reminder_assignee_pgsql_repo.find_by_reminder_and_user(
            reminder_id=reminder_id,
            user_id=user.id,
        )
        if assignment is None:
            msg = 'You are not authorized to update this reminder'
            raise AuthorizationError(msg)

        payload = schema.model_dump(exclude_unset=True)
        allowed = {'status'}
        disallowed = set(payload.keys()) - allowed
        if disallowed:
            msg = f'Assignees may only update the status field (got: {disallowed})'
            raise AuthorizationError(msg)

        updated_reminder = reminder.update(payload=payload, user=user)
        return await self.repos.reminder_pgsql_repo.update(entity=updated_reminder)

    async def _process_update_with_notification_and_assignees(
        self,
        payload: dict,
        reminder: ReminderEntity,
        user: UserEntity,
        *,
        new_assignee_ids: list[uuid.UUID] | None = None,
        notify_new_assignees: bool = False,
        assignee_scheduled_time: dt | None = None,
    ) -> ReminderEntity:
        """Process update when an explicit user notification (user_id) is requested.

        This encapsulates the long flow that updates the reminder, creates/sends
        or schedules a notification for a user, and then syncs assignees.
        """
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
        updated_reminder = reminder.update(payload=payload, user=user)
        updated_reminder = await self.repos.reminder_pgsql_repo.update(entity=updated_reminder)

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

        if new_assignee_ids is not None:
            await self._sync_assignees(
                reminder=updated_reminder,
                new_ids=new_assignee_ids,
                assigned_by=user.id,
                notify=notify_new_assignees,
                scheduled_time=assignee_scheduled_time,
            )
        return updated_reminder

    async def delete_reminder_by_id(self, reminder_id: uuid.UUID, caller: UserEntity) -> None:
        """Delete a reminder by id.

        For group reminders: only admin/owner/creator can delete.
        For personal reminders: only the owner can delete.
        """
        reminder = await self.repos.reminder_pgsql_repo.find_by_id(reminder_id=reminder_id)
        if reminder is None:
            msg = 'Reminder not found'
            raise BadRequestError(msg) from None

        if reminder.group_id is not None:
            # Group reminder — check role
            membership = await self.repos.group_member_pgsql_repo.find_by_group_and_user(
                group_id=reminder.group_id,
                user_id=caller.id,
            )
            is_creator = reminder.owner_id == caller.id
            is_privileged = membership is not None and membership.role in (
                MemberRoles.ADMIN,
                MemberRoles.OWNER,
            )
            if not is_creator and not is_privileged:
                msg = 'Only the reminder creator, group admin, or owner can delete this reminder'
                raise AuthorizationError(msg)
        elif reminder.owner_id != caller.id:
            msg = 'You can only delete your own reminders'
            raise AuthorizationError(msg)

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

        # Attach assignee user ids — deduplicate by user_id (keep latest)
        assignees_raw = await self.repos.reminder_assignee_pgsql_repo.list_by_reminder_id(reminder_id=reminder.id)
        seen_users: dict = {}
        for a in assignees_raw:
            uid = str(a.user_id)
            if uid not in seen_users or a.assigned_at > seen_users[uid].assigned_at:
                seen_users[uid] = a
        assignees = list(seen_users.values())
        reminder_dict['assignees'] = list(seen_users.keys())

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
                    'acknowledged_at': a.acknowledged_at,
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
