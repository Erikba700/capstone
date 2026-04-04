from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """Query parameters for pagination."""

    size: int = Field(default=20, gt=0, le=100_000)
    page: int = Field(default=1, gt=0)
