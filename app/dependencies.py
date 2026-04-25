import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import (
    OAuth2PasswordBearer,
)
from jose import JWTError, jwt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession as PgsqlSession

from app import services
from app.config import settings
from app.db.transaction_context import transaction_context
from app.entities import UserEntity
from app.repos import RepoFactory
from app.schemas.user_schemas import TokenPayloadSchema


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
    ) as pgsql_session:
        yield RepoFactory(pgsql_session)


reusable_oauth = OAuth2PasswordBearer(tokenUrl='/login', scheme_name='JWT')


async def get_current_user(
    repos: Annotated[RepoFactory, Depends(get_repo)],
    token: str = Depends(reusable_oauth),
) -> UserEntity:
    """Get authenticated user from credentials."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.algorithm])
        token_data = TokenPayloadSchema(**payload)

        if datetime.fromtimestamp(timestamp=token_data.exp, tz=UTC) < datetime.now(UTC):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Token expired',
                headers={'WWW-Authenticate': 'Bearer'},
            ) from None
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Could not validate credentials',
            headers={'WWW-Authenticate': 'Bearer'},
        ) from None
    service = services.UserService(repos=repos)
    user = await service.fetch_user_by_id(uuid.UUID(token_data.sub))

    return user
