"""Secure signed tokens for reminder acknowledgement email callbacks.

Tokens are short-lived JWTs signed with the app's jwt_secret_key.
Payload: { "sub": "<assignment_id>", "uid": "<user_id>", "act": "acknowledge"|"complete", "exp": ... }
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Literal

from jose import JWTError, jwt

from app.config import settings

_ALGORITHM = 'HS256'
_TOKEN_TTL_DAYS = 7

CallbackAction = Literal['acknowledge', 'complete']
ReassignmentAction = Literal['accept', 'reject']


def generate_callback_token(
    assignment_id: uuid.UUID,
    user_id: uuid.UUID,
    action: CallbackAction,
) -> str:
    """Generate a signed, expiring token for an email callback action.

    Args:
        assignment_id: UUID of the reminder assignment.
        user_id: UUID of the intended recipient (assignee).
        action: Either 'acknowledge' or 'complete'.

    Returns:
        Signed JWT string.
    """
    expire = datetime.now(UTC) + timedelta(days=_TOKEN_TTL_DAYS)
    payload = {
        'sub': str(assignment_id),
        'uid': str(user_id),
        'act': action,
        'exp': expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=_ALGORITHM)


def decode_callback_token(token: str) -> dict:
    """Decode and validate a callback token.

    Args:
        token: Signed JWT string produced by generate_callback_token.

    Returns:
        Dict with keys: sub (assignment_id str), uid (user_id str), act (action str).

    Raises:
        ValueError: If token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[_ALGORITHM])
        return payload
    except JWTError as exc:
        msg = 'Invalid or expired callback token'
        raise ValueError(msg) from exc


def generate_reassignment_token(
    request_id: uuid.UUID,
    assignee_id: uuid.UUID,
    action: ReassignmentAction,
) -> str:
    """Generate a signed token for a reassignment accept/reject email link.

    Args:
        request_id: UUID of the reassignment request.
        assignee_id: UUID of the current assignee who will act.
        action: Either 'accept' or 'reject'.

    Returns:
        Signed JWT string valid for 7 days.
    """
    expire = datetime.now(UTC) + timedelta(days=_TOKEN_TTL_DAYS)
    payload = {
        'sub': str(request_id),
        'uid': str(assignee_id),
        'act': action,
        'typ': 'reassignment',
        'exp': expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=_ALGORITHM)


def decode_reassignment_token(token: str) -> dict:
    """Decode and validate a reassignment callback token.

    Returns:
        Dict with keys: sub (request_id), uid (assignee_id), act (action).

    Raises:
        ValueError: If token is invalid, expired, or wrong type.
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[_ALGORITHM])
        if payload.get('typ') != 'reassignment':
            msg = 'Wrong token type'
            raise ValueError(msg)
        return payload
    except JWTError as exc:
        msg = 'Invalid or expired reassignment token'
        raise ValueError(msg) from exc
