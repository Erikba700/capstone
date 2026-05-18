"""Secure signed tokens for password reset email links.

Tokens are short-lived JWTs signed with the app's jwt_secret_key.
Payload: { "sub": "<user_id>", "typ": "password_reset", "exp": ... }
"""

import uuid
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from app.config import settings

_ALGORITHM = 'HS256'
_TOKEN_TTL_MINUTES = 30


def generate_password_reset_token(user_id: uuid.UUID) -> str:
    """Generate a signed, short-lived token for password reset.

    Args:
        user_id: UUID of the user requesting the password reset.

    Returns:
        Signed JWT string valid for 30 minutes.
    """
    expire = datetime.now(UTC) + timedelta(minutes=_TOKEN_TTL_MINUTES)
    payload = {
        'sub': str(user_id),
        'typ': 'password_reset',
        'exp': expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=_ALGORITHM)


def decode_password_reset_token(token: str) -> uuid.UUID:
    """Decode and validate a password reset token.

    Args:
        token: Signed JWT string produced by generate_password_reset_token.

    Returns:
        user_id UUID extracted from the token.

    Raises:
        ValueError: If token is invalid, expired, or wrong type.
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[_ALGORITHM])
    except JWTError as exc:
        msg = 'Invalid or expired password reset token'
        raise ValueError(msg) from exc

    if payload.get('typ') != 'password_reset':
        msg = 'Invalid token type'
        raise ValueError(msg)

    return uuid.UUID(payload['sub'])
