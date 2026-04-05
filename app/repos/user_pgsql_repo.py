import structlog
from sqlalchemy import exists, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Insert, Select, Update

from app.entities import UserEntity
from app.exceptions import BadRequestError, CreateObjectError
from app.models import Users

logger = structlog.getLogger(__name__)


class UserPgsqlQueries:
    """Space for user PostgreSQL queries."""

    @staticmethod
    def select_user_by_email_query(email: str) -> Select:
        """Select user by email."""
        return select(Users).where(Users.email == email)

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

    async def email_exists(self, email: str) -> bool:
        """Check if a user with the given oid exists."""
        query = self.queries.check_user_exists_query(email=email)
        res = await self.session.scalar(query)

        logger.info(f'User exists check for email={email}: {res}')

        return bool(res)

    async def find_by_username(
        self,
        email: str,
    ) -> UserEntity | None:
        """Find user or return None."""
        query = self.queries.select_user_by_email_query(email=email)
        instance = await self.session.scalar(query)

        logger.info(f'Found user for oid={email}: {instance is not None}')

        if instance is not None:
            return UserEntity.model_validate(instance)

        return None

    async def insert(self, entity: UserEntity) -> UserEntity:
        """Insert user to db."""
        data = entity.model_dump(include=Users.get_model_fields())
        query = self.queries.insert_user_query(user_data=data)
        instance = await self.session.scalar(query)

        if instance is None:
            logger.error('Insert returned no instance', id=entity.id)
            msg = 'Failed to insert user'
            raise CreateObjectError(msg)

        logger.info(f'Inserted user with id={entity.id}')

        return UserEntity.model_validate(instance)

    async def update(self, entity: UserEntity) -> UserEntity:
        """Update user in db."""
        data = entity.model_dump(include=Users.get_model_fields())
        query = self.queries.update_user_query(user_data=data)
        instance = await self.session.scalar(query)

        if instance is None:
            logger.error('Update returned no instance', id=entity.id)
            msg = 'Failed to update user'
            raise BadRequestError(msg)

        logger.info(f'Updated user with oid={entity.id}')

        return UserEntity.model_validate(instance)
