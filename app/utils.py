import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import jwt
from passlib.context import CryptContext

from app.config import settings
from app.exceptions import DomainError
from app.structs.error_structs import ErrorMessage


def get_utc_now() -> datetime:
    """Get current datetime in UTC."""
    return datetime.now(UTC)


def convert_to_utc(dt: datetime, from_timezone: str) -> datetime:
    """Convert a datetime from a specific timezone to UTC.

    Args:
        dt: Datetime to convert (can be naive or aware)
        from_timezone: Timezone string (e.g., 'Asia/Yerevan', 'America/New_York')

    Returns:
        Timezone-aware datetime in UTC
    """
    try:
        tz = ZoneInfo(from_timezone)
    except Exception as e:
        msg = f'Invalid timezone: {from_timezone}'
        raise ValueError(msg) from e

    # If datetime is naive, localize it to the source timezone
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    # If datetime is already aware but in a different timezone, convert it
    elif dt.tzinfo != tz:
        dt = dt.astimezone(tz)

    # Convert to UTC
    return dt.astimezone(UTC)


def convert_from_utc(dt: datetime, to_timezone: str) -> datetime:
    """Convert a UTC datetime to a specific timezone.

    Args:
        dt: UTC datetime (should be timezone-aware)
        to_timezone: Target timezone string (e.g., 'Asia/Yerevan', 'America/New_York')

    Returns:
        Timezone-aware datetime in the target timezone
    """
    try:
        tz = ZoneInfo(to_timezone)
    except Exception as e:
        msg = f'Invalid timezone: {to_timezone}'
        raise ValueError(msg) from e

    # If datetime is naive, assume it's UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)

    # Convert to target timezone
    return dt.astimezone(tz)


def validate_timezone(timezone_str: str) -> bool:
    """Validate if a timezone string is valid.

    Args:
        timezone_str: Timezone string to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        ZoneInfo(timezone_str)
        return True
    except Exception:
        return False


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
    subject: uuid.UUID,
) -> str:
    """Create access token."""
    expires_delta = get_utc_now() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode = {'exp': expires_delta, 'sub': str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, settings.algorithm)
    return encoded_jwt


def create_refresh_token(
    subject: uuid.UUID,
) -> str:
    """Create refresh token."""
    expires_delta = get_utc_now() + timedelta(minutes=settings.refresh_token_expire_minutes)

    to_encode = {'exp': expires_delta, 'sub': str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.jwt_refresh_secret_key, settings.algorithm)
    return encoded_jwt
