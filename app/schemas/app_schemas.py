from app.schemas.base_schemas import BaseSchema
from app.structs.app_structs import BuildInfo


class AppInfoResponseSchema(BaseSchema):
    """Schema for application info response."""

    build: BuildInfo
