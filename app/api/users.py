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
    UserSignUpRequestSchema,
    UserSignUpResponseSchema,
)
from app.services import UserService
from app.utils import (
    create_access_token,
    create_refresh_token,
    get_hashed_password,
    verify_password,
)

router = APIRouter(tags=['Users'])


@router.post(
    '/signup', summary='Create new user', response_model=UserSignUpResponseSchema
)
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

    hashed_password = get_hashed_password(schema.password)
    new_user_data = UserEntity.create_new(
        name=schema.name,
        email=schema.email,
        hashed_password=hashed_password,
    )
    new_user = await service.insert_user(entity=new_user_data)

    return new_user


@router.get('/user', response_model=UserEntity)  # noqa: FAST001
async def get_authenticated_user(
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> UserEntity:
    """Get user data."""
    return user


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
