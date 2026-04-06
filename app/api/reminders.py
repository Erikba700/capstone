from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import (
    get_shared_tx_repo,
)
from app.entities.reminder import ReminderEntity
from app.repos import RepoFactory
from app.schemas.reminder_schemas import (
    RemindersCreateRequestSchema,
    RemindersCreateResponseSchema,
)
from app.services.reminder_service import ReminderService

router = APIRouter(tags=['Reminders'])


@router.post(
    '/reminders',
    summary='Create new reminder',
    response_model=RemindersCreateResponseSchema,
)
async def create_reminder(
    schema: RemindersCreateRequestSchema,
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> ReminderEntity:
    """Create new reminder."""
    service = ReminderService(repos=repos)
    # Build entity and persist
    reminder_entity = ReminderEntity.create_new(
        title=schema.title,
        description=schema.description,
        owner_id=schema.owner_id,
        is_completed=schema.is_completed,
    )

    created_reminder = await service.create_reminder(entity=reminder_entity)
    return created_reminder


# @router.get('/user', response_model=UserEntity)
# async def get_authenticated_user(
#     user: Annotated[UserEntity, Depends(get_current_user)],
# ) -> UserEntity:
#     """Get user data."""
#     return user
#
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
