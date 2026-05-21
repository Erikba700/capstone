"""Group reminder collaboration service.

Provides Jira-style collaborative task management for group reminders:
- Strict validation (assignees/notifications must be group members)
- Role-based permissions (member vs admin/owner)
- Self-assignment and reassignment flows
- Group-wide and targeted notifications
"""

import uuid
from datetime import UTC
from datetime import datetime as dt

import structlog

from app.entities import NotificationEntity, UserEntity
from app.entities.group_members import GroupMembersEntity, MemberRoles
from app.entities.reminder import ReminderEntity
from app.entities.reminder_assignee import ReminderAssigneeEntity
from app.exceptions import AuthorizationError, BadRequestError
from app.repos import RepoFactory
from app.services.notifications_service import NotificationService

logger = structlog.getLogger(__name__)


class GroupReminderService:
    """Collaborative group reminder logic."""

    def __init__(self, repos: RepoFactory) -> None:
        self.repos = repos

    # ── Validation helpers ────────────────────────────────────────────────────

    async def ensure_group_reminder(self, reminder: ReminderEntity) -> uuid.UUID:
        """Raise BadRequestError if reminder is not a group reminder. Return group_id."""
        if reminder.group_id is None:
            msg = 'This reminder does not belong to a group'
            raise BadRequestError(msg)
        return reminder.group_id

    async def ensure_group_member(
        self,
        group_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> GroupMembersEntity:
        """Raise AuthorizationError if user is not a member of the group."""
        membership = await self.repos.group_member_pgsql_repo.find_by_group_and_user(
            group_id=group_id,
            user_id=user_id,
        )
        if membership is None:
            msg = 'You are not a member of this group'
            raise AuthorizationError(msg)
        return membership

    async def ensure_group_assignment_allowed(
        self,
        group_id: uuid.UUID,
        assignee_id: uuid.UUID,
    ) -> GroupMembersEntity:
        """Ensure assignee is a group member. Raise BadRequestError otherwise."""
        membership = await self.repos.group_member_pgsql_repo.find_by_group_and_user(
            group_id=group_id,
            user_id=assignee_id,
        )
        if membership is None:
            msg = f'User {assignee_id} is not a member of this group and cannot be assigned'
            raise BadRequestError(msg)
        return membership

    async def ensure_group_notification_allowed(
        self,
        group_id: uuid.UUID,
        target_user_id: uuid.UUID,
    ) -> GroupMembersEntity:
        """Ensure notification target is a group member. Raise BadRequestError otherwise."""
        membership = await self.repos.group_member_pgsql_repo.find_by_group_and_user(
            group_id=group_id,
            user_id=target_user_id,
        )
        if membership is None:
            msg = f'User {target_user_id} is not a member of this group and cannot be notified'
            raise BadRequestError(msg)
        return membership

    async def ensure_group_reminder_edit_allowed(
        self,
        reminder: ReminderEntity,
        user: UserEntity,
        membership: GroupMembersEntity,
    ) -> None:
        """Allow edit if: owner/admin/creator of reminder/assignee. Raise otherwise."""
        # Admins and owners can always edit
        if membership.role in (MemberRoles.ADMIN, MemberRoles.OWNER):
            return
        # Creator can always edit their own reminder
        if reminder.owner_id == user.id:
            return
        # Assignee can edit if assigned to this reminder
        assignment = await self.repos.reminder_assignee_pgsql_repo.find_by_reminder_and_user(
            reminder_id=reminder.id,
            user_id=user.id,
        )
        if assignment is None:
            msg = 'You can only edit reminders you created or are assigned to'
            raise AuthorizationError(msg)

    # ── Assignment helpers ─────────────────────────────────────────────────────

    async def assign_user_to_reminder(
        self,
        reminder: ReminderEntity,
        assignee_id: uuid.UUID,
        assigned_by: uuid.UUID,
        *,
        notify: bool = False,
        notify_previous: bool = False,
        scheduled_time: dt | None = None,
    ) -> ReminderAssigneeEntity:
        """Add a group member as an assignee to a reminder (multi-assignee).

        Does NOT remove existing assignees — call remove_assignee separately.
        If the user is already assigned, returns the existing assignment.
        """
        group_id = await self.ensure_group_reminder(reminder)
        await self.ensure_group_assignment_allowed(group_id=group_id, assignee_id=assignee_id)

        # Avoid duplicate — return existing if already assigned
        existing = await self.repos.reminder_assignee_pgsql_repo.find_by_reminder_and_user(
            reminder_id=reminder.id,
            user_id=assignee_id,
        )
        if existing is not None:
            return existing

        entity = ReminderAssigneeEntity.create_new(
            reminder_id=reminder.id,
            user_id=assignee_id,
            assigned_by=assigned_by,
        )
        assignment = await self.repos.reminder_assignee_pgsql_repo.insert(entity=entity)
        logger.info('Assigned user to group reminder', reminder_id=reminder.id, assignee_id=assignee_id)

        if notify and assignee_id != assigned_by:
            assignee_user = await self.repos.user_pgsql_repo.find_by_id(assignee_id)
            assigner_user = await self.repos.user_pgsql_repo.find_by_id(assigned_by)
            if assignee_user is not None and assigner_user is not None:
                await self._send_notification(
                    user=assignee_user,
                    reminder=reminder,
                    message=f'You were assigned to "{reminder.title}" by {assigner_user.name}',
                    creator_email=assigner_user.email,
                    scheduled_time=scheduled_time,
                    assignment_id=assignment.id,
                )

        return assignment

    async def self_assign(
        self,
        reminder: ReminderEntity,
        user: UserEntity,
        *,
        notify_previous: bool = False,
        scheduled_time: dt | None = None,
    ) -> ReminderAssigneeEntity:
        """Add the current user as an assignee (multi-assignee — does not remove others)."""
        group_id = await self.ensure_group_reminder(reminder)
        await self.ensure_group_member(group_id=group_id, user_id=user.id)

        # Return existing if already assigned
        existing = await self.repos.reminder_assignee_pgsql_repo.find_by_reminder_and_user(
            reminder_id=reminder.id,
            user_id=user.id,
        )
        if existing is not None:
            return existing

        entity = ReminderAssigneeEntity.create_new(
            reminder_id=reminder.id,
            user_id=user.id,
            assigned_by=user.id,
        )
        return await self.repos.reminder_assignee_pgsql_repo.insert(entity=entity)

    # ── Notification helpers ───────────────────────────────────────────────────

    async def notify_assignees(
        self,
        reminder: ReminderEntity,
        sender: UserEntity,
        message: str | None = None,
        scheduled_time: dt | None = None,
    ) -> int:
        """Notify all current assignees of a group reminder. Returns count sent."""
        group_id = await self.ensure_group_reminder(reminder)
        await self.ensure_group_member(group_id=group_id, user_id=sender.id)

        assignments = await self.repos.reminder_assignee_pgsql_repo.list_by_reminder_id(
            reminder_id=reminder.id,
        )
        count = 0
        for assignment in assignments:
            if assignment.user_id == sender.id:
                continue
            await self.ensure_group_notification_allowed(group_id=group_id, target_user_id=assignment.user_id)
            target = await self.repos.user_pgsql_repo.find_by_id(assignment.user_id)
            if target is not None:
                msg = message or f'Reminder update: "{reminder.title}" by {sender.name}'
                await self._send_notification(
                    user=target,
                    reminder=reminder,
                    message=msg,
                    creator_email=sender.email,
                    scheduled_time=scheduled_time,
                )
                count += 1
        return count

    async def notify_all_members(
        self,
        reminder: ReminderEntity,
        sender: UserEntity,
        message: str | None = None,
        scheduled_time: dt | None = None,
    ) -> int:
        """Notify ALL group members about a reminder. Requires admin/owner. Returns count sent."""
        group_id = await self.ensure_group_reminder(reminder)
        membership = await self.ensure_group_member(group_id=group_id, user_id=sender.id)

        if membership.role not in (MemberRoles.ADMIN, MemberRoles.OWNER):
            msg = 'Only admins and owners can notify all group members'
            raise AuthorizationError(msg)

        members = await self.repos.group_member_pgsql_repo.list_by_group_id(group_id=group_id)
        count = 0
        for m in members:
            if m.user_id == sender.id:
                continue
            target = await self.repos.user_pgsql_repo.find_by_id(m.user_id)
            if target is not None:
                msg = message or f'Group reminder: "{reminder.title}" by {sender.name}'
                await self._send_notification(
                    user=target,
                    reminder=reminder,
                    message=msg,
                    creator_email=sender.email,
                    scheduled_time=scheduled_time,
                )
                count += 1
        return count

    async def _send_notification(
        self,
        user: UserEntity,
        reminder: ReminderEntity,
        message: str,
        creator_email: str,
        scheduled_time: dt | None = None,
        assignment_id: uuid.UUID | None = None,
    ) -> None:
        """Create and send a notification — immediate or scheduled.

        If assignment_id is provided and the notification is immediate, sends
        the HTML email with acknowledge/complete action buttons.
        """
        notification = NotificationEntity.create_new(
            user_id=user.id,
            reminder_id=reminder.id,
            message=message,
            creator_email=creator_email,
            scheduled_time=scheduled_time,
        )
        notification_service = NotificationService(repos=self.repos)
        created = await self.repos.notification_pgsql_repo.insert(notification)
        if scheduled_time is not None:
            # Notification already persisted above; no second insert needed.
            # The Celery beat job will pick it up by scheduled_time.
            logger.info('Scheduled group notification', user_id=user.id, reminder_id=reminder.id, at=scheduled_time)
        else:
            if assignment_id is not None:
                success = await notification_service.send_reminder_notification_with_actions(
                    user=user,
                    reminder=reminder,
                    notification=created,
                    assignment_id=assignment_id,
                )
            else:
                success = await notification_service.send_reminder_notification(
                    user=user,
                    reminder=reminder,
                    notification=created,
                )
            if success:
                await notification_service.mark_notification_as_sent(created)
                logger.info('Sent group notification', user_id=user.id, reminder_id=reminder.id)
            else:
                logger.error('Failed to send group notification', user_id=user.id, reminder_id=reminder.id)

    # ── Reminder update for group context ────────────────────────────────────

    async def update_group_reminder(
        self,
        reminder: ReminderEntity,
        payload: dict,
        user: UserEntity,
        membership: GroupMembersEntity,
        *,
        notify_assignees_on_update: bool = False,
        new_assignee_ids: list[uuid.UUID] | None = None,
        notify_new_assignees: bool = False,
        assignee_scheduled_time: dt | None = None,
    ) -> ReminderEntity:
        """Update a group reminder with role-based field access.

        Admin/owner can update all fields.
        Member can only update fields if creator or assignee.
        """
        is_privileged = membership.role in (MemberRoles.ADMIN, MemberRoles.OWNER)

        if not is_privileged and reminder.owner_id != user.id:
            assignment = await self.repos.reminder_assignee_pgsql_repo.find_by_reminder_and_user(
                reminder_id=reminder.id,
                user_id=user.id,
            )
            if assignment is None:
                msg = 'You can only edit reminders you created or are assigned to'
                raise AuthorizationError(msg)
            # Assignee-only: restrict to status
            allowed = {'status'}
            disallowed = set(payload.keys()) - allowed
            if disallowed:
                msg = f'Assignees without admin/owner role may only update status (got: {disallowed})'
                raise AuthorizationError(msg)

        # Strip non-reminder fields
        payload.pop('user_id', None)
        payload.pop('scheduled_time', None)

        updated = reminder.update(payload=payload, user=user)
        result = await self.repos.reminder_pgsql_repo.update(entity=updated)

        if notify_assignees_on_update:
            await self.notify_assignees(
                reminder=result,
                sender=user,
                message=f'"{result.title}" was updated by {user.name}',
            )

        if new_assignee_ids is not None:
            group_id = await self.ensure_group_reminder(reminder)
            # Validate every assignee is a group member
            for aid in new_assignee_ids:
                await self.ensure_group_assignment_allowed(group_id=group_id, assignee_id=aid)
            from app.services.reminder_service import ReminderService

            reminder_service = ReminderService(repos=self.repos)
            await reminder_service._sync_assignees(
                reminder=result,
                new_ids=new_assignee_ids,
                assigned_by=user.id,
                notify=notify_new_assignees,
                scheduled_time=assignee_scheduled_time,
            )

        return result

    async def complete_assignment(
        self,
        reminder: ReminderEntity,
        assignment: ReminderAssigneeEntity,
        user: UserEntity,
    ) -> ReminderAssigneeEntity:
        """Mark an assignment as completed and update reminder status."""
        group_id = await self.ensure_group_reminder(reminder)
        membership = await self.ensure_group_member(group_id=group_id, user_id=user.id)

        # Only the assignee themselves or admin/owner can mark completed
        if assignment.user_id != user.id and membership.role not in (MemberRoles.ADMIN, MemberRoles.OWNER):
            msg = 'Only the assignee or group admin/owner can complete this assignment'
            raise AuthorizationError(msg)

        now = dt.now(UTC)
        updated = assignment.model_copy(
            update={'completed_at': now, 'updated_at': now},
        )
        result = await self.repos.reminder_assignee_pgsql_repo.update(entity=updated)

        # Notify reminder creator about completion
        if reminder.owner_id != user.id:
            owner = await self.repos.user_pgsql_repo.find_by_id(reminder.owner_id)
            if owner is not None:
                await self._send_notification(
                    user=owner,
                    reminder=reminder,
                    message=f'{user.name} completed assignment for "{reminder.title}"',
                    creator_email=user.email,
                )

        return result
