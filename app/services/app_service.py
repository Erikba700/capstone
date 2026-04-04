from app.config import settings
from app.structs.app_structs import AppInfoEntity, BuildInfo


class AppInfoService:
    """Service to provide application related actions."""

    @classmethod
    async def get_app_info(cls) -> AppInfoEntity:
        """Get application info."""
        build_info = BuildInfo(
            version=settings.app_main_version,
            app_version=settings.app_version,
            name=settings.app_name,
        )
        return AppInfoEntity(build=build_info)
