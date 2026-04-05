from pydantic import BaseModel, computed_field

from app.utils import get_utc_now


class BuildInfo(BaseModel):
    """Schema build info response."""

    version: str
    app_version: str
    name: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def time(self) -> str:
        """Get build time in ISO format."""
        return get_utc_now().isoformat()


class AppInfoEntity(BaseModel):
    """Entity for application info."""

    build: BuildInfo
