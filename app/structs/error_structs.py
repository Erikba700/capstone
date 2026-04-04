from pydantic import BaseModel


class ErrorMessage(BaseModel):
    """Schema for error messages returned by FastAPI."""

    detail: str
