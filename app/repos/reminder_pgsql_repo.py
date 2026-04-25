import uuid

import structlog
from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Insert, Select, Update

from app.entities.reminder import ReminderEntity
from app.exceptions import NotFoundError
from app.models import Reminders

logger = structlog.getLogger(__name__)


class ReminderPgsqlQueries:
    """SQL builder for reminders."""

    @staticmethod
    def select_reminder_by_reminder_id_query(reminder_id: uuid.UUID) -> Select:
        """Select a reminder by its id."""
        return select(Reminders).where(Reminders.id == reminder_id)

    @staticmethod
    def insert_reminder_query(reminder_data: dict) -> Insert:
        """Insert a new reminder query."""
        return insert(Reminders).values(**reminder_data).returning(Reminders)

    @staticmethod
    def update_reminder_query(reminder_data: dict) -> Update:
        """Update a reminder query."""
        return update(Reminders).values(**reminder_data).where(Reminders.id == reminder_data['id']).returning(Reminders)

    @staticmethod
    def select_reminders_by_owner_id_query(
        owner_id: uuid.UUID,
        filters: dict,
    ) -> Select:
        """Select reminders by owner id."""
        query = select(Reminders).where(Reminders.owner_id == owner_id)

        for filter_name, filter_value in filters.items():
            column = getattr(Reminders, filter_name)
            query = query.where(column.is_(filter_value) if isinstance(filter_value, bool) else column == filter_value)

        query = query.order_by(Reminders.created_at.desc())

        return query


class ReminderPgsqlRepo:
    """Postgres persistence for reminders."""

    def __init__(
        self,
        session: AsyncSession,
        queries: type[ReminderPgsqlQueries] = ReminderPgsqlQueries,
    ) -> None:
        self.session = session
        self.queries = queries

    async def find_by_id(self, reminder_id: uuid.UUID) -> ReminderEntity | None:
        """Find a reminder by its id. Returns None if not found."""
        query = self.queries.select_reminder_by_reminder_id_query(reminder_id=reminder_id)
        instance = await self.session.scalar(query)

        logger.info('Found reminder', reminder_id=reminder_id, found=(instance is not None))

        if instance is None:
            return None

        return ReminderEntity.model_validate(instance)

    async def insert(self, entity: ReminderEntity) -> ReminderEntity:
        """Insert a new reminder."""
        data = entity.model_dump(include=Reminders.get_model_fields())
        query = self.queries.insert_reminder_query(reminder_data=data)
        result = await self.session.execute(query)
        instance = result.scalar_one_or_none()

        if instance is None:
            logger.error('Insert returned no instance for reminder', id=entity.id)
            msg = 'Failed to insert reminder'
            raise RuntimeError(msg) from None

        logger.info('Inserted reminder', id=entity.id)
        return ReminderEntity.model_validate(instance)

    async def fetch_reminders_by_owner_id(
        self,
        owner_id: uuid.UUID,
        filters: dict,
    ) -> list[ReminderEntity]:
        """Fetch reminders by owner id."""
        query = self.queries.select_reminders_by_owner_id_query(
            owner_id=owner_id,
            filters=filters,
        )
        result = await self.session.execute(query)
        instances = result.scalars().all()

        logger.info(
            'Fetched reminders by owner id',
            owner_id=owner_id,
            count=len(instances),
        )

        return [ReminderEntity.model_validate(instance) for instance in instances]

    async def update(self, entity: ReminderEntity) -> ReminderEntity:
        """Update a reminder."""
        data = entity.model_dump(include=Reminders.get_model_fields())
        query = self.queries.update_reminder_query(reminder_data=data)

        try:
            result = await self.session.execute(query)
            instance = result.scalar_one_or_none()
        except IntegrityError as e:
            msg = 'Related object not found'
            raise NotFoundError(msg) from e

        logger.info('Updated reminder', id=entity.id)

        return ReminderEntity.model_validate(instance)

    async def delete_by_id(self, reminder_id: uuid.UUID) -> None:
        """Delete a reminder by its id."""
        query = self.queries.select_reminder_by_reminder_id_query(reminder_id=reminder_id)
        instance = await self.session.scalar(query)
        await self.session.delete(instance)
        logger.info('Deleted reminder', reminder=instance)
