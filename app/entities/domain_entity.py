import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.utils import get_utc_now


class DomainEntity(BaseModel):
    """Base for all domain entities."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def generate_id() -> uuid.UUID:
        """Generate business id for entity."""
        return uuid.uuid4()

    @staticmethod
    def generate_current_timestamp() -> datetime:
        """Generate timestamp with timezone."""
        return get_utc_now()
