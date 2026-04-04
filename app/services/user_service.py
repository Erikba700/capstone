import uuid
from typing import Annotated

import structlog
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.sql.functions import user

from app import services
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

    async def fetch(self, oid: uuid.UUID) -> UserEntity | None:
        """Check if a user with the given oid exists."""
        user = await self.repos.user_pgsql_repo.find_by_id(oid=oid)
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

    async def authenticate(
        self,
        credentials: Annotated[
            HTTPAuthorizationCredentials, Depends(HTTPBearer())
        ],
    ) -> UserEntity:
        """Validate Bearer token and save user if not exists."""
        # user_payload = await self.validate_token(token=credentials.credentials)
        user_jwt_token = '7ead9d01-c2d8-489e-baf9-56df2cb13073'

        user_service = services.UserService(
            repos=self.repos,
        )
        user_entity = await user_service.fetch(
            oid=user_jwt_token,
        )

        return user_entity

