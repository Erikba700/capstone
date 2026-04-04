from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base for all application schemas."""

    model_config = ConfigDict(frozen=True)
