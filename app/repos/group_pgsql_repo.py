import uuid

import structlog
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Insert, Select, Update

from app.entities.group import GroupEntity
from app.models.groups import Groups

logger = structlog.getLogger(__name__)


class GroupPgsqlQueries:
    """SQL builder for groups."""

    @staticmethod
    def insert_group_query(data: dict) -> Insert:
        """Insert a new group."""
        return insert(Groups).values(**data).returning(Groups)

    @staticmethod
    def select_by_id_query(group_id: uuid.UUID) -> Select:
        """Select group by id."""
        return select(Groups).where(Groups.id == group_id)

    @staticmethod
    def select_by_owner_id_query(owner_id: uuid.UUID) -> Select:
        """Select groups owned by a user."""
        return select(Groups).where(Groups.owner_id == owner_id).order_by(Groups.created_at.desc())

    @staticmethod
    def update_group_query(data: dict) -> Update:
        """Update a group."""
        return update(Groups).values(**data).where(Groups.id == data['id']).returning(Groups)


class GroupPgsqlRepo:
    """Postgres persistence for groups."""

    def __init__(
        self,
        session: AsyncSession,
        queries: type[GroupPgsqlQueries] = GroupPgsqlQueries,
    ) -> None:
        self.session = session
        self.queries = queries

    async def insert(self, entity: GroupEntity) -> GroupEntity:
        """Insert a new group."""
        data = entity.model_dump(include=Groups.get_model_fields())
        query = self.queries.insert_group_query(data=data)
        result = await self.session.execute(query)
        instance = result.scalar_one_or_none()
        if instance is None:
            msg = 'Failed to insert group'
            raise RuntimeError(msg)
        logger.info('Inserted group', id=entity.id)
        return GroupEntity.model_validate(instance)

    async def find_by_id(self, group_id: uuid.UUID) -> GroupEntity | None:
        """Find group by id."""
        query = self.queries.select_by_id_query(group_id=group_id)
        instance = await self.session.scalar(query)
        if instance is None:
            return None
        return GroupEntity.model_validate(instance)

    async def list_by_owner_id(self, owner_id: uuid.UUID) -> list[GroupEntity]:
        """List groups owned by a user."""
        query = self.queries.select_by_owner_id_query(owner_id=owner_id)
        result = await self.session.execute(query)
        instances = result.scalars().all()
        return [GroupEntity.model_validate(i) for i in instances]

    async def update(self, entity: GroupEntity) -> GroupEntity:
        """Update a group."""
        data = entity.model_dump(include=Groups.get_model_fields())
        query = self.queries.update_group_query(data=data)
        result = await self.session.execute(query)
        instance = result.scalar_one_or_none()
        if instance is None:
            msg = 'Failed to update group'
            raise RuntimeError(msg)
        logger.info('Updated group', id=entity.id)
        return GroupEntity.model_validate(instance)

    async def delete_by_id(self, group_id: uuid.UUID) -> None:
        """Delete a group by id."""
        query = self.queries.select_by_id_query(group_id=group_id)
        instance = await self.session.scalar(query)
        if instance is not None:
            await self.session.delete(instance)
            logger.info('Deleted group', id=group_id)
