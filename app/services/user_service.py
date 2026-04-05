import structlog

from app.entities import UserEntity
from app.exceptions import NotFoundError
from app.repos import RepoFactory

logger = structlog.getLogger(__name__)


class UserService:
    """User use cases."""

    def __init__(
        self,
        repos: RepoFactory,
    ) -> None:
        self.repos = repos

    async def check_user_email_exists(self, email: str) -> bool:
        """Check if a user with the given email exists."""
        exists = await self.repos.user_pgsql_repo.email_exists(email=email)
        return exists

    async def fetch_user_by_email(self, email: str) -> UserEntity:
        """Check if a user with the given email."""
        user = await self.repos.user_pgsql_repo.find_by_username(email=email)
        if user is None:
            raise NotFoundError()
        return user

    async def insert_user(self, entity: UserEntity) -> UserEntity:
        """Check if a user with the given oid exists."""
        user = await self.repos.user_pgsql_repo.insert(entity=entity)
        return user

    async def update_user(self, entity: UserEntity) -> UserEntity:
        """Update an existing user."""
        user = await self.repos.user_pgsql_repo.update(entity=entity)
        return user
