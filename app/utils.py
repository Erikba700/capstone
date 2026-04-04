from datetime import UTC, datetime
from typing import Any
from passlib.context import CryptContext

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


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_hashed_password(password: str) -> str:
    return password_context.hash(password)

def verify_password(password: str, hashed_pass: str) -> bool:
    return password_context.verify(password, hashed_pass)
