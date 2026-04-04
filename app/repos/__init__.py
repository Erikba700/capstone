from sqlalchemy.ext.asyncio import AsyncSession as PgsqlSession

from .user_pgsql_repo import UserPgsqlRepo


class RepoFactory:
    """Helper factory for all repos."""

    def __init__(
        self,
        pgsql_session: PgsqlSession,
    ) -> None:
        self.pgsql_session = pgsql_session

    @property
    def user_pgsql_repo(self) -> UserPgsqlRepo:
        """Init PostgreSQL repo for users."""
        return UserPgsqlRepo(self.pgsql_session)



__all__ = [
    'RepoFactory',
    'UserPgsqlRepo',
]
