import structlog
from fastapi import APIRouter

from app import services
from app.config import settings
from app.schemas.app_schemas import AppInfoResponseSchema
from app.structs.app_structs import AppInfoEntity

router = APIRouter(tags=['Core'])


@router.get('/health', status_code=204)
async def get_health() -> None:
    """Simple endpoint to ping the app to."""
    structlog.contextvars.bind_contextvars(ignore=True)


@router.get('/version')
async def get_version() -> str:
    """Get version of the application as raw string."""
    return settings.app_version


@router.get('/actuator/info', response_model=AppInfoResponseSchema)
async def get_actuator_info() -> AppInfoEntity:
    """Get application info."""
    return await services.AppInfoService.get_app_info()
