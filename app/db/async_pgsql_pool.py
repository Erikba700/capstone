from sqlalchemy.engine.url import URL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.util import immutabledict

from app.config import settings
from app.db.async_abstract_pool import AbstractAsyncPool


class AsyncPostgresPool(AbstractAsyncPool):
    """Asynchronous PostgreSQL connection pool based on SQLAlchemy.

    Connection parameters are taken from app.config.settings:
        - pgsql_host
        - pgsql_port
        - pgsql_user
        - pgsql_password
        - pgsql_db_name

    Attributes:
        _url (URL): SQLAlchemy URL for database connection.
        _engine (AsyncEngine): SQLAlchemy asynchronous engine.
        _session_pool (async_sessionmaker): Factory for asynchronous sessions.

    For FastAPI integration and usage:
        app.state.pgsql_session_pool = AsyncPostgresPool()

        async with pgsql_session_pool.get_session() as session:
            result = await session.execute(...)

    Methods:
        get_session(): Returns a new async session.
        close(): Closes the connection pool and all connections.
    """

    def __init__(self) -> None:
        self._url = URL(
            drivername='postgresql+asyncpg',
            username=settings.pgsql_user,
            password=settings.pgsql_password,
            host=settings.pgsql_host,
            port=settings.pgsql_port,
            database=settings.pgsql_db_name,
            query=immutabledict(),
        )
        self._engine: AsyncEngine = create_async_engine(
            url=self._url,
            pool_size=10,  # up to x db connections
            max_overflow=10,  # allow y more connections in overflow
        )
        self._session_pool = async_sessionmaker(bind=self._engine)

    def get_session(self) -> AsyncSession:
        """Returns a new async session (use with 'async with').

        Session will be created in any available connection.
        """
        return self._session_pool()

    async def close(self) -> None:
        """Close connection pool and all connections."""
        await self._engine.dispose()
