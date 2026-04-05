from collections.abc import AsyncGenerator
from contextlib import AsyncExitStack, asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession as SqlSession

from app.db.async_pgsql_pool import AsyncPostgresPool


@asynccontextmanager
async def transaction_context(
    pgsql_pool: AsyncPostgresPool,
) -> AsyncGenerator[SqlSession]:
    """Enter transactional state for both PostgreSQL and Neo4j.

    On any exception raised, cancels both.
    """
    # Create a session from the pool and begin a transaction. We must
    # yield the session to the caller so the code executed inside the
    # `async with transaction_context(...) as session:` block runs within
    # the same transactional scope. The transaction will be committed
    # if the block exits normally or rolled back on exception.
    async with AsyncExitStack() as stack:
        pgsql_session = await stack.enter_async_context(pgsql_pool.get_session())

        # Enter the transaction context manager so commit/rollback is
        # handled around the yielded session.
        await stack.enter_async_context(pgsql_session.begin())
        try:
            yield pgsql_session
            await pgsql_session.commit()
        except Exception:
            # Explicit rollback for clarity (session.begin() will also
            # rollback on exception), then re-raise so callers see the
            # original error.
            await pgsql_session.rollback()
            raise
