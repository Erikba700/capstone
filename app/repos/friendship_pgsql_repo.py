import uuid

import structlog
from sqlalchemy import and_, delete, insert, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Delete, Insert, Select, Update

from app.entities.friendship import FriendshipEntity, FriendshipStatus
from app.models.friendships import Friendships

logger = structlog.getLogger(__name__)


class FriendshipPgsqlQueries:
    """SQL builder for friendships."""

    @staticmethod
    def insert_query(data: dict) -> Insert:
        """Insert a new friendship."""
        return insert(Friendships).values(**data).returning(Friendships)

    @staticmethod
    def select_by_id_query(friendship_id: uuid.UUID) -> Select:
        """Select friendship by id."""
        return select(Friendships).where(Friendships.id == friendship_id)

    @staticmethod
    def select_between_users_query(user_a: uuid.UUID, user_b: uuid.UUID) -> Select:
        """Select friendship between two users (either direction)."""
        return select(Friendships).where(
            or_(
                and_(Friendships.requester_id == user_a, Friendships.addressee_id == user_b),
                and_(Friendships.requester_id == user_b, Friendships.addressee_id == user_a),
            )
        )

    @staticmethod
    def select_incoming_query(user_id: uuid.UUID) -> Select:
        """Select pending incoming friend requests for a user."""
        return (
            select(Friendships)
            .where(
                Friendships.addressee_id == user_id,
                Friendships.status == FriendshipStatus.PENDING,
            )
            .order_by(Friendships.created_at.desc())
        )

    @staticmethod
    def select_outgoing_query(user_id: uuid.UUID) -> Select:
        """Select pending outgoing friend requests from a user."""
        return (
            select(Friendships)
            .where(
                Friendships.requester_id == user_id,
                Friendships.status == FriendshipStatus.PENDING,
            )
            .order_by(Friendships.created_at.desc())
        )

    @staticmethod
    def select_friends_query(user_id: uuid.UUID) -> Select:
        """Select all accepted friendships for a user."""
        return (
            select(Friendships)
            .where(
                or_(
                    Friendships.requester_id == user_id,
                    Friendships.addressee_id == user_id,
                ),
                Friendships.status == FriendshipStatus.ACCEPTED,
            )
            .order_by(Friendships.accepted_at.desc())
        )

    @staticmethod
    def update_query(data: dict) -> Update:
        """Update a friendship record."""
        return update(Friendships).values(**data).where(Friendships.id == data['id']).returning(Friendships)

    @staticmethod
    def delete_by_id_query(friendship_id: uuid.UUID) -> Delete:
        """Delete a friendship by id."""
        return delete(Friendships).where(Friendships.id == friendship_id)


class FriendshipPgsqlRepo:
    """Postgres persistence for friendships."""

    def __init__(
        self,
        session: AsyncSession,
        queries: type[FriendshipPgsqlQueries] = FriendshipPgsqlQueries,
    ) -> None:
        self.session = session
        self.queries = queries

    async def insert(self, entity: FriendshipEntity) -> FriendshipEntity:
        """Insert a new friendship."""
        data = entity.model_dump(include=Friendships.get_model_fields())
        query = self.queries.insert_query(data=data)
        result = await self.session.execute(query)
        instance = result.scalar_one_or_none()
        if instance is None:
            msg = 'Failed to insert friendship'
            raise RuntimeError(msg)
        logger.info('Inserted friendship', id=entity.id)
        return FriendshipEntity.model_validate(instance)

    async def find_by_id(self, friendship_id: uuid.UUID) -> FriendshipEntity | None:
        """Find friendship by id."""
        query = self.queries.select_by_id_query(friendship_id=friendship_id)
        instance = await self.session.scalar(query)
        if instance is None:
            return None
        return FriendshipEntity.model_validate(instance)

    async def find_between_users(
        self,
        user_a: uuid.UUID,
        user_b: uuid.UUID,
    ) -> FriendshipEntity | None:
        """Find any friendship row between two users (either direction)."""
        query = self.queries.select_between_users_query(user_a=user_a, user_b=user_b)
        instance = await self.session.scalar(query)
        if instance is None:
            return None
        return FriendshipEntity.model_validate(instance)

    async def list_incoming(self, user_id: uuid.UUID) -> list[FriendshipEntity]:
        """List pending incoming friend requests."""
        query = self.queries.select_incoming_query(user_id=user_id)
        result = await self.session.execute(query)
        return [FriendshipEntity.model_validate(i) for i in result.scalars().all()]

    async def list_outgoing(self, user_id: uuid.UUID) -> list[FriendshipEntity]:
        """List pending outgoing friend requests."""
        query = self.queries.select_outgoing_query(user_id=user_id)
        result = await self.session.execute(query)
        return [FriendshipEntity.model_validate(i) for i in result.scalars().all()]

    async def list_friends(self, user_id: uuid.UUID) -> list[FriendshipEntity]:
        """List all accepted friendships."""
        query = self.queries.select_friends_query(user_id=user_id)
        result = await self.session.execute(query)
        return [FriendshipEntity.model_validate(i) for i in result.scalars().all()]

    async def update(self, entity: FriendshipEntity) -> FriendshipEntity:
        """Update a friendship record."""
        data = entity.model_dump(include=Friendships.get_model_fields())
        query = self.queries.update_query(data=data)
        result = await self.session.execute(query)
        instance = result.scalar_one_or_none()
        if instance is None:
            msg = 'Failed to update friendship'
            raise RuntimeError(msg)
        logger.info('Updated friendship', id=entity.id)
        return FriendshipEntity.model_validate(instance)

    async def delete_by_id(self, friendship_id: uuid.UUID) -> None:
        """Hard-delete a friendship by id."""
        query = self.queries.delete_by_id_query(friendship_id=friendship_id)
        await self.session.execute(query)
        logger.info('Deleted friendship', id=friendship_id)
