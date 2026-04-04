import uuid

import structlog
from sqlalchemy import exists, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Insert, Select, Update

from app.entities import UserEntity
from app.models import Users

logger = structlog.getLogger(__name__)


class UserPgsqlQueries:
    """Space for user PostgreSQL queries."""

    @staticmethod
    def select_user_by_oid_query(oid: uuid.UUID) -> Select:
        """Select user by oid."""
        return select(Users).where(Users.id == oid)

    @staticmethod
    def check_user_exists_query(email: str) -> Select:
        """Select to check if user exists by email."""
        return select(exists().where(Users.email == email))

    @staticmethod
    def insert_user_query(user_data: dict) -> Insert:
        """Insert a new user."""
        return insert(Users).values(**user_data).returning(Users)

    @staticmethod
    def update_user_query(user_data: dict) -> Update:
        """Update a user."""
        return (
            update(Users)
            .values(**user_data)
            .where(Users.id == user_data['id'])
            .returning(Users)
        )


class UserPgsqlRepo:
    """User persistence layer for PostgreSQL."""

    def __init__(
        self,
        session: AsyncSession,
        queries: type[UserPgsqlQueries] = UserPgsqlQueries,
    ) -> None:
        self.session = session
        self.queries = queries

    async def email_exists(self, email: uuid.UUID) -> bool:
        """Check if a user with the given oid exists."""
        query = self.queries.check_user_exists_query(email=email)
        res = await self.session.scalar(query)

        logger.info(f'User exists check for email={email}: {res}')

        return bool(res)

    async def find_by_id(
        self,
        oid: uuid.UUID,
    ) -> UserEntity | None:
        """Find user or return None."""
        query = self.queries.select_user_by_oid_query(oid=oid)
        instance = await self.session.scalar(query)

        logger.info(f'Found user for oid={oid}: {instance is not None}')

        if instance is not None:
            return UserEntity.model_validate(instance)

        return None

    async def insert(self, entity: UserEntity) -> UserEntity:
        """Insert user to db."""
        data = entity.model_dump(include=Users.get_model_fields())
        query = self.queries.insert_user_query(user_data=data)
        result = await self.session.execute(query)
        instance = result.scalar_one_or_none()
        print(f"asdfasdf {instance}")

        if instance is None:
            # If no row was returned, something went wrong with insertion —
            # raise an error to make the failure visible to the caller.
            logger.error('Insert returned no instance', id=entity.id)
            raise RuntimeError('Failed to insert user')

        logger.info(f'Inserted user with id={entity.id}')

        return UserEntity.model_validate(instance)

    async def update(self, entity: UserEntity) -> UserEntity:
        """Update user in db."""
        data = entity.model_dump(include=Users.get_model_fields())
        query = self.queries.update_user_query(user_data=data)
        result = await self.session.execute(query)
        instance = result.scalar_one_or_none()

        if instance is None:
            logger.error('Update returned no instance', id=entity.id)
            raise RuntimeError('Failed to update user')

        logger.info(f'Updated user with oid={entity.id}')

        return UserEntity.model_validate(instance)
