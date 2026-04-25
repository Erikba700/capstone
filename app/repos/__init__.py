from sqlalchemy.ext.asyncio import AsyncSession as PgsqlSession

from .notifications_pgsql_repo import NotificationPgsqlRepo
from .reminder_pgsql_repo import ReminderPgsqlRepo
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

    @property
    def reminder_pgsql_repo(self) -> ReminderPgsqlRepo:
        """Init PostgreSQL repo for reminders."""
        return ReminderPgsqlRepo(self.pgsql_session)

    @property
    def notification_pgsql_repo(self) -> NotificationPgsqlRepo:
        """Init PostgreSQL repo for notifications."""
        return NotificationPgsqlRepo(self.pgsql_session)


__all__ = [
    'NotificationPgsqlRepo',
    'ReminderPgsqlRepo',
    'RepoFactory',
    'UserPgsqlRepo',
]
