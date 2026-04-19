import uuid

import structlog

from app.entities.reminder import ReminderEntity
from app.exceptions import BadRequestError
from app.repos import RepoFactory
from app.schemas.reminder_schemas import RemindersFiltersSchema

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

    async def get_reminders_by_owner_id(
        self,
        owner_id: uuid.UUID,
        filters: RemindersFiltersSchema,
    ) -> list[ReminderEntity]:
        """Fetch reminders by owner id."""
        reminders_dict = filters.model_dump(exclude_none=True)
        reminders = await self.repos.reminder_pgsql_repo.fetch_reminders_by_owner_id(
            owner_id=owner_id,
            filters=reminders_dict,
        )
        return reminders

    async def delete_reminder_by_id(self, reminder_id: uuid.UUID) -> None:
        """Delete a reminder by id."""
        reminder = await self.repos.reminder_pgsql_repo.find_by_id(
            reminder_id=reminder_id
        )
        if reminder is None:
            msg = 'Reminder not found'
            raise BadRequestError(msg) from None
        await self.repos.reminder_pgsql_repo.delete_by_id(reminder_id=reminder.id)
