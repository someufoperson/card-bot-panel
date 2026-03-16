from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.redis import get_redis
from app.schemas.setting import SettingBulkUpdate, SettingResponse, SettingUpdate
from app.services.settings_service import SettingsService

router = APIRouter()


def _get_service(
    session: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis),
) -> SettingsService:
    return SettingsService(session, redis)


@router.get("", response_model=list[SettingResponse])
async def list_settings(service: SettingsService = Depends(_get_service)):
    return await service.get_all()


@router.get("/{key}", response_model=SettingResponse)
async def get_setting(key: str, service: SettingsService = Depends(_get_service)):
    return await service.get_by_key(key)


@router.put("/{key}", response_model=SettingResponse)
async def update_setting(
    key: str,
    data: SettingUpdate,
    service: SettingsService = Depends(_get_service),
):
    return await service.update(key, data.value)


@router.put("", response_model=list[SettingResponse])
async def bulk_update_settings(
    data: SettingBulkUpdate,
    service: SettingsService = Depends(_get_service),
):
    return await service.bulk_update(data.settings)
