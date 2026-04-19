import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.dependencies import (
    get_current_user,
    get_repo,
    get_shared_tx_repo,
)
from app.entities import UserEntity
from app.entities.reminder import ReminderEntity
from app.repos import RepoFactory
from app.schemas.reminder_schemas import (
    RemindersCreateRequestSchema,
    RemindersFiltersSchema,
    RemindersListResponseSchema,
    RemindersResponseSchema,
)
from app.services.reminder_service import ReminderService

router = APIRouter(tags=['Reminders'])


@router.post(
    '/reminders',
    summary='Create new reminder',
    response_model=RemindersResponseSchema,
)
async def create_reminder(
    user: Annotated[UserEntity, Depends(get_current_user)],
    schema: RemindersCreateRequestSchema,
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> ReminderEntity:
    """Create new reminder."""
    service = ReminderService(repos=repos)

    reminder_entity = ReminderEntity.create_new(
        title=schema.title,
        description=schema.description,
        owner_id=user.id,
        is_completed=schema.is_completed,
    )

    created_reminder = await service.create_reminder(entity=reminder_entity)
    return created_reminder


@router.post('/reminders/search', response_model=RemindersListResponseSchema)
async def get_reminders(
    filters: RemindersFiltersSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_repo)],
) -> dict[str, list[ReminderEntity]]:
    """Get all reminders for a user."""
    service = ReminderService(repos=repos)
    reminders = await service.get_reminders_by_owner_id(
        owner_id=user.id,
        filters=filters,
    )
    return {'reminders': reminders}


@router.delete('/reminders/{reminder_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_reminder(
    reminder_id: uuid.UUID,
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> None:
    """Delete a reminder by id."""
    service = ReminderService(repos=repos)
    await service.delete_reminder_by_id(
        reminder_id=reminder_id,
    )
