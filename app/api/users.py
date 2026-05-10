from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.dependencies import (
    get_current_user,
    get_repo,
    get_shared_tx_repo,
)
from app.entities import UserEntity
from app.exceptions import BadRequestError
from app.repos import RepoFactory
from app.schemas.user_schemas import (
    UserLoginResponseSchema,
    UserProfileResponseSchema,
    UserSignUpRequestSchema,
    UserSignUpResponseSchema,
    UserUpdateRequestSchema,
)
from app.services import UserService
from app.utils import (
    create_access_token,
    create_refresh_token,
    get_hashed_password,
    validate_timezone,
    verify_password,
)

router = APIRouter(tags=['Users'])


@router.post('/signup', summary='Create new user', response_model=UserSignUpResponseSchema)
async def create_user(
    schema: UserSignUpRequestSchema,
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> UserEntity:
    """Create new user."""
    # querying database to check if user already exist
    service = UserService(repos=repos)
    user = await service.check_user_email_exists(schema.email)
    if user:
        msg = 'User with this email already exist'
        raise BadRequestError(msg) from None

    # Validate timezone
    if not validate_timezone(schema.timezone):
        msg = (
            f'Invalid timezone: {schema.timezone}. '
            'Please use a valid IANA timezone (e.g., UTC, Asia/Yerevan, America/New_York)'
        )
        raise BadRequestError(msg) from None

    hashed_password = get_hashed_password(schema.password)
    new_user_data = UserEntity.create_new(
        name=schema.name,
        email=schema.email,
        hashed_password=hashed_password,
        timezone=schema.timezone,
    )
    new_user = await service.insert_user(entity=new_user_data)

    return new_user


@router.get('/user', response_model=UserEntity)  # noqa: FAST001
async def get_authenticated_user(
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> UserEntity:
    """Get user data."""
    return user


@router.patch('/user/profile', response_model=UserProfileResponseSchema)
async def update_profile(
    schema: UserUpdateRequestSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> UserEntity:
    """Update authenticated user profile (name, timezone, password)."""
    service = UserService(repos=repos)
    payload: dict = {}

    if schema.name is not None:
        payload['name'] = schema.name

    if schema.timezone is not None:
        if not validate_timezone(schema.timezone):
            msg = f'Invalid timezone: {schema.timezone}. Please use a valid IANA timezone (e.g., UTC, Asia/Yerevan)'
            raise BadRequestError(msg) from None
        payload['timezone'] = schema.timezone

    if schema.new_password is not None:
        if schema.current_password is None:
            msg = 'current_password is required to set a new password'
            raise BadRequestError(msg) from None
        if not verify_password(schema.current_password, user.hashed_password):
            msg = 'Current password is incorrect'
            raise BadRequestError(msg) from None
        payload['hashed_password'] = get_hashed_password(schema.new_password)

    if not payload:
        msg = 'No fields to update'
        raise BadRequestError(msg) from None

    updated_user = await service.update_profile(user=user, payload=payload)
    return updated_user


@router.post(
    '/login',
    summary='Create access and refresh tokens for user',
    response_model=UserLoginResponseSchema,
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    repos: Annotated[RepoFactory, Depends(get_repo)],
) -> dict:
    """Authenticate user and return access and refresh tokens."""
    service = UserService(repos=repos)
    user = await service.fetch_user_by_email(form_data.username)
    if user is None:
        msg = 'Incorrect email or password'
        raise BadRequestError(msg) from None

    hashed_pass = user.hashed_password
    if not verify_password(form_data.password, hashed_pass):
        msg = 'Incorrect email or password'
        raise BadRequestError(msg) from None

    return {
        'access_token': create_access_token(user.id),
        'refresh_token': create_refresh_token(user.id),
    }
