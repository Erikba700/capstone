import uuid

import structlog
from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Insert, Select, Update

from app.entities import NotificationEntity
from app.exceptions import NotFoundError
from app.models import NotificationRecipients

logger = structlog.getLogger(__name__)


class NotificationPgsqlQueries:
    """SQL builder for notifications."""

    @staticmethod
    def select_notification_by_id_query(notification_id: uuid.UUID) -> Select:
        """Select a notification by its id."""
        return select(NotificationRecipients).where(NotificationRecipients.id == notification_id)

    @staticmethod
    def insert_notification_query(notification_data: dict) -> Insert:
        """Insert a new notification query."""
        return insert(NotificationRecipients).values(**notification_data).returning(NotificationRecipients)

    @staticmethod
    def update_notification_query(notification_data: dict) -> Update:
        """Update a notification query."""
        return (
            update(NotificationRecipients)
            .values(**notification_data)
            .where(NotificationRecipients.id == notification_data['id'])
            .returning(NotificationRecipients)
        )

    @staticmethod
    def select_notifications_by_user_id_query(
        user_id: uuid.UUID,
        filters: dict,
    ) -> Select:
        """Select notifications by user id."""
        query = select(NotificationRecipients).where(NotificationRecipients.user_id == user_id)

        for filter_name, filter_value in filters.items():
            column = getattr(NotificationRecipients, filter_name)
            query = query.where(column.is_(filter_value) if isinstance(filter_value, bool) else column == filter_value)

        query = query.order_by(NotificationRecipients.created_at.desc())

        return query

    @staticmethod
    def select_notifications_by_reminder_id_query(
        reminder_id: uuid.UUID,
    ) -> Select:
        """Select notifications by reminder id."""
        return (
            select(NotificationRecipients)
            .where(NotificationRecipients.reminder_id == reminder_id)
            .order_by(NotificationRecipients.created_at.desc())
        )


class NotificationPgsqlRepo:
    """Postgres persistence for notifications."""

    def __init__(
        self,
        session: AsyncSession,
        queries: type[NotificationPgsqlQueries] = NotificationPgsqlQueries,
    ) -> None:
        self.session = session
        self.queries = queries

    async def find_by_id(self, notification_id: uuid.UUID) -> NotificationEntity | None:
        """Find a notification by its id. Returns None if not found."""
        query = self.queries.select_notification_by_id_query(notification_id=notification_id)
        instance = await self.session.scalar(query)

        logger.info(
            'Found notification',
            notification_id=notification_id,
            found=(instance is not None),
        )

        if instance is None:
            return None

        return NotificationEntity.model_validate(instance)

    async def insert(self, entity: NotificationEntity) -> NotificationEntity:
        """Insert a new notification."""
        data = entity.model_dump(include=NotificationRecipients.get_model_fields())
        query = self.queries.insert_notification_query(notification_data=data)

        try:
            result = await self.session.execute(query)
            instance = result.scalar_one_or_none()
        except IntegrityError as e:
            msg = 'Related object not found (user_id or reminder_id invalid)'
            logger.error('Failed to insert notification', error=str(e))
            raise NotFoundError(msg) from e

        if instance is None:
            logger.error('Insert returned no instance for notification', id=entity.id)
            msg = 'Failed to insert notification'
            raise RuntimeError(msg) from None

        logger.info('Inserted notification', id=entity.id)
        return NotificationEntity.model_validate(instance)

    async def fetch_notifications_by_user_id(
        self,
        user_id: uuid.UUID,
        filters: dict | None = None,
    ) -> list[NotificationEntity]:
        """Fetch notifications by user id."""
        if filters is None:
            filters = {}

        query = self.queries.select_notifications_by_user_id_query(
            user_id=user_id,
            filters=filters,
        )
        result = await self.session.execute(query)
        instances = result.scalars().all()

        logger.info(
            'Fetched notifications by user id',
            user_id=user_id,
            count=len(instances),
        )

        return [NotificationEntity.model_validate(instance) for instance in instances]

    async def fetch_notifications_by_reminder_id(
        self,
        reminder_id: uuid.UUID,
    ) -> list[NotificationEntity]:
        """Fetch notifications by reminder id."""
        query = self.queries.select_notifications_by_reminder_id_query(reminder_id=reminder_id)
        result = await self.session.execute(query)
        instances = result.scalars().all()

        logger.info(
            'Fetched notifications by reminder id',
            reminder_id=reminder_id,
            count=len(instances),
        )

        return [NotificationEntity.model_validate(instance) for instance in instances]

    async def update(self, entity: NotificationEntity) -> NotificationEntity:
        """Update a notification."""
        data = entity.model_dump(include=NotificationRecipients.get_model_fields())
        query = self.queries.update_notification_query(notification_data=data)

        try:
            result = await self.session.execute(query)
            instance = result.scalar_one_or_none()
        except IntegrityError as e:
            msg = 'Related object not found'
            raise NotFoundError(msg) from e

        if instance is None:
            logger.error('Update returned no instance for notification', id=entity.id)
            msg = 'Notification not found'
            raise NotFoundError(msg) from None

        logger.info('Updated notification', id=entity.id)

        return NotificationEntity.model_validate(instance)

    async def delete_by_id(self, notification_id: uuid.UUID) -> None:
        """Delete a notification by its id."""
        query = self.queries.select_notification_by_id_query(notification_id=notification_id)
        instance = await self.session.scalar(query)

        if instance is None:
            msg = f'Notification with id {notification_id} not found'
            raise NotFoundError(msg)

        await self.session.delete(instance)
        logger.info('Deleted notification', notification_id=notification_id)
