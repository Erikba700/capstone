from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession as PgsqlSession

from app import services
from app.db.transaction_context import transaction_context
from app.entities import UserEntity
from app.repos import RepoFactory


async def get_pgsql_session(request: Request) -> AsyncGenerator[PgsqlSession]:
    """Get a new async PostgreSQL session."""
    pool = request.app.state.pgsql_session_pool
    async with pool.get_session() as session:
        yield session


async def get_repo(
    pgsql_session: Annotated[PgsqlSession, Depends(get_pgsql_session)],
) -> AsyncGenerator[RepoFactory]:
    """Get repo with regular sessions."""
    yield RepoFactory(pgsql_session)


async def get_shared_tx_repo(request: Request) -> AsyncGenerator[RepoFactory]:
    """Get repo with transaction shared between PostgreSQL and Neo4j."""
    async with transaction_context(
        request.app.state.pgsql_session_pool,
    ) as (pgsql_session):
        yield RepoFactory(pgsql_session)


async def get_authenticated_user(
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
    credentials: Annotated[
        HTTPAuthorizationCredentials, Depends(HTTPBearer())
    ],
) -> UserEntity:
    """Get authenticated user from credentials, init service."""
    service = services.UserService(repos=repos,)
    return await service.authenticate(
        credentials=credentials,
    )
