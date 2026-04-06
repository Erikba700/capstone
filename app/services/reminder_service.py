import uuid

import structlog

from app.entities.reminder import ReminderEntity
from app.exceptions import BadRequestError
from app.repos import RepoFactory

logger = structlog.getLogger(__name__)


class ReminderService:
    """Reminder use cases."""

    def __init__(
        self,
        repos: RepoFactory,
    ) -> None:
        self.repos = repos

    async def create_reminder(self, entity: ReminderEntity) -> ReminderEntity:
        """Create a new reminder.

        Validates that owner exists before insertion because owner_id is a FK
        to users table.
        """
        owner_id = uuid.UUID(str(entity.owner_id))

        owner = await self.repos.user_pgsql_repo.find_by_id(owner_id)
        if owner is None:
            msg = 'Owner not found'
            raise BadRequestError(msg) from None

        reminder = await self.repos.reminder_pgsql_repo.insert(entity=entity)
        return reminder
