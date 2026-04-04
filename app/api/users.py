import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import (
    get_authenticated_user,
    get_repo,
    get_shared_tx_repo,
)
from app.entities import UserEntity
from app.repos import RepoFactory
from app.schemas.user_schemas import UserSignUpResponseSchema, UserSignUpRequestSchema, UserResponseSchema
from app.services import UserService
from fastapi import status, HTTPException
from app.utils import get_hashed_password

router = APIRouter(tags=['Users'])

@router.post('/signup', summary="Create new user", response_model=UserSignUpResponseSchema)
async def create_user(
        schema: UserSignUpRequestSchema,
        repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
      ) -> UserEntity:
    # querying database to check if user already exist
    service = UserService(repos=repos)
    user = await service.check_user_email_exists(schema.email)
    if user:
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exist"
        )
    hashed_password = get_hashed_password(schema.password)
    new_user = UserEntity.create_new(
        name=schema.name,
        email=schema.email,
        hashed_password=hashed_password,
    )
    user = await service.insert_user(entity=new_user)

    return user


@router.get('/user', response_model=UserResponseSchema)
async def get_authenticated_user(
    user: Annotated[UserEntity, Depends(get_authenticated_user)],
) -> UserEntity:
    """Get user data."""
    return user

