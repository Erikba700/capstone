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
    ForgotPasswordRequestSchema,
    MessageResponseSchema,
    ResetPasswordRequestSchema,
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
from app.utils.password_reset_tokens import (
    decode_password_reset_token,
    generate_password_reset_token,
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


@router.post('/forgot-password', response_model=MessageResponseSchema, summary='Request a password reset email')
async def forgot_password(
    schema: ForgotPasswordRequestSchema,
    repos: Annotated[RepoFactory, Depends(get_repo)],
) -> dict:
    """Send a password reset link to the user's email address.

    Always returns a success message regardless of whether the email exists,
    to prevent user enumeration.
    """
    from app.config import settings as _settings
    from app.services.notifications_service import NotificationService

    # `service` is not needed here; only the notification service is used.
    notification_service = NotificationService(repos=repos)

    user = await repos.user_pgsql_repo.find_by_username(email=schema.email)
    if user is not None:
        token = generate_password_reset_token(user.id)
        reset_url = f'{_settings.frontend_url}/reset-password?token={token}'
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
          <h2 style="color: #1f2937;">Reset Your Password</h2>
          <p style="color: #4b5563;">You requested a password reset for your Remindly account.</p>
          <p style="color: #4b5563;">
            Click the button below to set a new password.
            This link expires in <strong>30 minutes</strong>.
          </p>
          <div style="text-align: center; margin: 32px 0;">
            <a href="{reset_url}"
               style="background-color: #6366f1; color: white; padding: 14px 28px;
                      border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 16px;">
              Reset Password
            </a>
          </div>
          <p style="color: #9ca3af; font-size: 13px;">
            If you did not request a password reset, you can safely ignore this email.
          </p>
          <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;" />
          <p style="color: #9ca3af; font-size: 12px;">Remindly — reminder management app</p>
        </div>
        """
        await notification_service.send_custom_notification(
            recipient=schema.email,
            subject='Reset your Remindly password',
            message=html_body,
            html_content=html_body,
        )

    return {'message': 'If an account with that email exists, a password reset link has been sent.'}


@router.post('/reset-password', response_model=MessageResponseSchema, summary='Reset password using a token')
async def reset_password(
    schema: ResetPasswordRequestSchema,
    repos: Annotated[RepoFactory, Depends(get_shared_tx_repo)],
) -> dict:
    """Reset a user's password given a valid signed reset token."""
    try:
        user_id = decode_password_reset_token(schema.token)
    except ValueError as exc:
        raise BadRequestError(str(exc)) from exc

    service = UserService(repos=repos)
    user = await service.fetch_user_by_id(user_id)

    updated = user.update(payload={'hashed_password': get_hashed_password(schema.new_password)})
    await repos.user_pgsql_repo.update(entity=updated)

    return {'message': 'Password has been reset successfully. You can now log in with your new password.'}
