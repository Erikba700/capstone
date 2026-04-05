from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from passlib.context import CryptContext

from app.config import settings
from app.exceptions import DomainError
from app.structs.error_structs import ErrorMessage


def get_utc_now() -> datetime:
    """Get current datetime in UTC."""
    return datetime.now(UTC)


def generate_responses_for_error(
    *errors: type[DomainError],
) -> dict[int | str, dict[str, Any]]:
    """Helper to generate possible response errors for OpenAPI schema."""
    return {
        error.status_code: {
            'model': ErrorMessage,
            'description': error.default_message,
        }
        for error in errors
    }


password_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def get_hashed_password(password: str) -> str:
    """Hash password."""
    return password_context.hash(password)


def verify_password(password: str, hashed_pass: str) -> bool:
    """Verify password."""
    return password_context.verify(password, hashed_pass)


def create_access_token(
    subject: str,
) -> str:
    """Create access token."""
    expires_delta = get_utc_now() + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    to_encode = {'exp': expires_delta, 'sub': str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, settings.algorithm)
    return encoded_jwt


def create_refresh_token(
    subject: str,
) -> str:
    """Create refresh token."""
    expires_delta = get_utc_now() + timedelta(
        minutes=settings.refresh_token_expire_minutes
    )

    to_encode = {'exp': expires_delta, 'sub': str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_refresh_secret_key, settings.algorithm
    )
    return encoded_jwt
