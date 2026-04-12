from typing import Annotated

from fastapi import APIRouter, Depends

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


#
# @router.post(
#     '/login',
#     summary='Create access and refresh tokens for user',
#     response_model=UserLoginResponseSchema,
# )
# async def login(
#     form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
#     repos: Annotated[RepoFactory, Depends(get_repo)],
# ) -> dict:
#     """Authenticate user and return access and refresh tokens."""
#     service = UserService(repos=repos)
#     user = await service.fetch_user_by_email(form_data.username)
#     if user is None:
#         msg = 'Incorrect email or password'
#         raise BadRequestError(msg) from None
#
#     hashed_pass = user.hashed_password
#     if not verify_password(form_data.password, hashed_pass):
#         msg = 'Incorrect email or password'
#         raise BadRequestError(msg) from None
#
#     return {
#         'access_token': create_access_token(user.id),
#         'refresh_token': create_refresh_token(user.id),
#     }
