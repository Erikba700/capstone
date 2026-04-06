import uuid

import structlog
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Insert, Select, Update

from app.entities.reminder import ReminderEntity
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
        return (
            update(Reminders)
            .values(**reminder_data)
            .where(Reminders.id == reminder_data['id'])
            .returning(Reminders)
        )


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
        query = self.queries.select_reminder_by_reminder_id_query(
            reminder_id=reminder_id
        )
        instance = await self.session.scalar(query)

        logger.info(
            'Found reminder', reminder_id=reminder_id, found=(instance is not None)
        )

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
