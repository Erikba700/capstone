import uuid

import structlog
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Insert, Select, Update

from app.entities.group_members import GroupMembersEntity, MemberRoles
from app.models.group_members import GroupMembers

logger = structlog.getLogger(__name__)


class GroupMemberPgsqlQueries:
    """SQL builder for group members."""

    @staticmethod
    def insert_member_query(data: dict) -> Insert:
        """Insert a new group member."""
        return insert(GroupMembers).values(**data).returning(GroupMembers)

    @staticmethod
    def select_by_id_query(member_id: uuid.UUID) -> Select:
        """Select member by id."""
        return select(GroupMembers).where(GroupMembers.id == member_id)

    @staticmethod
    def select_by_group_id_query(group_id: uuid.UUID) -> Select:
        """Select all members of a group."""
        return select(GroupMembers).where(GroupMembers.group_id == group_id).order_by(GroupMembers.joined_at.asc())

    @staticmethod
    def select_by_group_and_user_query(group_id: uuid.UUID, user_id: uuid.UUID) -> Select:
        """Select a specific membership."""
        return select(GroupMembers).where(
            GroupMembers.group_id == group_id,
            GroupMembers.user_id == user_id,
        )

    @staticmethod
    def select_by_user_id_query(user_id: uuid.UUID) -> Select:
        """Select all memberships for a user."""
        return select(GroupMembers).where(GroupMembers.user_id == user_id)

    @staticmethod
    def update_member_query(data: dict) -> Update:
        """Update a group member record."""
        return update(GroupMembers).values(**data).where(GroupMembers.id == data['id']).returning(GroupMembers)

    @staticmethod
    def count_owners_query(group_id: uuid.UUID) -> Select:
        """Count owners in a group (to prevent removing last owner)."""
        return select(GroupMembers).where(
            GroupMembers.group_id == group_id,
            GroupMembers.role == MemberRoles.OWNER,
        )


class GroupMemberPgsqlRepo:
    """Postgres persistence for group members."""

    def __init__(
        self,
        session: AsyncSession,
        queries: type[GroupMemberPgsqlQueries] = GroupMemberPgsqlQueries,
    ) -> None:
        self.session = session
        self.queries = queries

    async def insert(self, entity: GroupMembersEntity) -> GroupMembersEntity:
        """Insert a new group member."""
        data = entity.model_dump(include=GroupMembers.get_model_fields())
        query = self.queries.insert_member_query(data=data)
        result = await self.session.execute(query)
        instance = result.scalar_one_or_none()
        if instance is None:
            msg = 'Failed to insert group member'
            raise RuntimeError(msg)
        logger.info('Inserted group member', id=entity.id)
        return GroupMembersEntity.model_validate(instance)

    async def find_by_id(self, member_id: uuid.UUID) -> GroupMembersEntity | None:
        """Find member record by id."""
        query = self.queries.select_by_id_query(member_id=member_id)
        instance = await self.session.scalar(query)
        if instance is None:
            return None
        return GroupMembersEntity.model_validate(instance)

    async def find_by_group_and_user(self, group_id: uuid.UUID, user_id: uuid.UUID) -> GroupMembersEntity | None:
        """Find a specific membership."""
        query = self.queries.select_by_group_and_user_query(group_id=group_id, user_id=user_id)
        instance = await self.session.scalar(query)
        if instance is None:
            return None
        return GroupMembersEntity.model_validate(instance)

    async def list_by_group_id(self, group_id: uuid.UUID) -> list[GroupMembersEntity]:
        """List all members of a group."""
        query = self.queries.select_by_group_id_query(group_id=group_id)
        result = await self.session.execute(query)
        instances = result.scalars().all()
        return [GroupMembersEntity.model_validate(i) for i in instances]

    async def list_by_user_id(self, user_id: uuid.UUID) -> list[GroupMembersEntity]:
        """List all group memberships for a user."""
        query = self.queries.select_by_user_id_query(user_id=user_id)
        result = await self.session.execute(query)
        instances = result.scalars().all()
        return [GroupMembersEntity.model_validate(i) for i in instances]

    async def update(self, entity: GroupMembersEntity) -> GroupMembersEntity:
        """Update a group member record."""
        data = entity.model_dump(include=GroupMembers.get_model_fields())
        query = self.queries.update_member_query(data=data)
        result = await self.session.execute(query)
        instance = result.scalar_one_or_none()
        if instance is None:
            msg = 'Failed to update group member'
            raise RuntimeError(msg)
        logger.info('Updated group member', id=entity.id)
        return GroupMembersEntity.model_validate(instance)

    async def delete_by_id(self, member_id: uuid.UUID) -> None:
        """Delete a group member record by id."""
        query = self.queries.select_by_id_query(member_id=member_id)
        instance = await self.session.scalar(query)
        if instance is not None:
            await self.session.delete(instance)
            logger.info('Deleted group member', id=member_id)

    async def count_owners(self, group_id: uuid.UUID) -> int:
        """Count owners in a group."""
        query = self.queries.count_owners_query(group_id=group_id)
        result = await self.session.execute(query)
        return len(result.scalars().all())
