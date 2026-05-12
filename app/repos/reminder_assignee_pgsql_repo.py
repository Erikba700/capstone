import uuid

import structlog
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Insert, Select, Update

from app.entities.reminder_assignee import ReminderAssigneeEntity
from app.models.reminder_assignees import ReminderAssignees

logger = structlog.getLogger(__name__)


class ReminderAssigneePgsqlQueries:
    """SQL builder for reminder assignees."""

    @staticmethod
    def insert_assignee_query(data: dict) -> Insert:
        """Insert a new reminder assignee."""
        return insert(ReminderAssignees).values(**data).returning(ReminderAssignees)

    @staticmethod
    def select_by_id_query(assignee_id: uuid.UUID) -> Select:
        """Select assignee by id."""
        return select(ReminderAssignees).where(ReminderAssignees.id == assignee_id)

    @staticmethod
    def select_by_reminder_id_query(reminder_id: uuid.UUID) -> Select:
        """Select all assignees for a reminder."""
        return (
            select(ReminderAssignees)
            .where(ReminderAssignees.reminder_id == reminder_id)
            .order_by(ReminderAssignees.assigned_at.asc())
        )

    @staticmethod
    def select_by_user_id_query(user_id: uuid.UUID) -> Select:
        """Select all reminder assignments for a user."""
        return (
            select(ReminderAssignees)
            .where(ReminderAssignees.user_id == user_id)
            .order_by(ReminderAssignees.assigned_at.desc())
        )

    @staticmethod
    def update_assignee_query(data: dict) -> Update:
        """Update an assignee record."""
        return (
            update(ReminderAssignees)
            .values(**data)
            .where(ReminderAssignees.id == data['id'])
            .returning(ReminderAssignees)
        )

    @staticmethod
    def select_by_reminder_and_user_query(
        reminder_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Select:
        """Select a specific assignment by reminder and user."""
        return select(ReminderAssignees).where(
            ReminderAssignees.reminder_id == reminder_id,
            ReminderAssignees.user_id == user_id,
        )


class ReminderAssigneePgsqlRepo:
    """Postgres persistence for reminder assignees."""

    def __init__(
        self,
        session: AsyncSession,
        queries: type[ReminderAssigneePgsqlQueries] = ReminderAssigneePgsqlQueries,
    ) -> None:
        self.session = session
        self.queries = queries

    async def insert(self, entity: ReminderAssigneeEntity) -> ReminderAssigneeEntity:
        """Insert a new reminder assignee."""
        data = entity.model_dump(include=ReminderAssignees.get_model_fields())
        query = self.queries.insert_assignee_query(data=data)
        result = await self.session.execute(query)
        instance = result.scalar_one_or_none()

        if instance is None:
            msg = 'Failed to insert reminder assignee'
            raise RuntimeError(msg)

        logger.info('Inserted reminder assignee', id=entity.id)
        return ReminderAssigneeEntity.model_validate(instance)

    async def find_by_id(self, assignee_id: uuid.UUID) -> ReminderAssigneeEntity | None:
        """Find assignee by id."""
        query = self.queries.select_by_id_query(assignee_id=assignee_id)
        instance = await self.session.scalar(query)
        if instance is None:
            return None
        return ReminderAssigneeEntity.model_validate(instance)

    async def list_by_reminder_id(self, reminder_id: uuid.UUID) -> list[ReminderAssigneeEntity]:
        """List all assignees for a given reminder."""
        query = self.queries.select_by_reminder_id_query(reminder_id=reminder_id)
        result = await self.session.execute(query)
        instances = result.scalars().all()
        logger.info('Listed assignees for reminder', reminder_id=reminder_id, count=len(instances))
        return [ReminderAssigneeEntity.model_validate(i) for i in instances]

    async def list_by_user_id(self, user_id: uuid.UUID) -> list[ReminderAssigneeEntity]:
        """List all reminder assignments for a user."""
        query = self.queries.select_by_user_id_query(user_id=user_id)
        result = await self.session.execute(query)
        instances = result.scalars().all()
        logger.info('Listed reminder assignments for user', user_id=user_id, count=len(instances))
        return [ReminderAssigneeEntity.model_validate(i) for i in instances]

    async def find_by_reminder_and_user(
        self,
        reminder_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ReminderAssigneeEntity | None:
        """Find a specific assignment by reminder and user."""
        query = self.queries.select_by_reminder_and_user_query(
            reminder_id=reminder_id,
            user_id=user_id,
        )
        instance = await self.session.scalar(query)
        if instance is None:
            return None
        return ReminderAssigneeEntity.model_validate(instance)

    async def update(self, entity: ReminderAssigneeEntity) -> ReminderAssigneeEntity:
        """Update an assignee record."""
        data = entity.model_dump(include=ReminderAssignees.get_model_fields())
        query = self.queries.update_assignee_query(data=data)
        result = await self.session.execute(query)
        instance = result.scalar_one_or_none()

        if instance is None:
            msg = 'Failed to update reminder assignee'
            raise RuntimeError(msg)

        logger.info('Updated reminder assignee', id=entity.id)
        return ReminderAssigneeEntity.model_validate(instance)

    async def delete_by_id(self, assignee_id: uuid.UUID) -> None:
        """Delete an assignee record by id."""
        query = self.queries.select_by_id_query(assignee_id=assignee_id)
        instance = await self.session.scalar(query)
        if instance is not None:
            await self.session.delete(instance)
            logger.info('Deleted reminder assignee', id=assignee_id)
