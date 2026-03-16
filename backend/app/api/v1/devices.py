from fastapi import APIRouter, Depends
from redis.asyncio import Redis

from app.core.redis import get_redis
from app.schemas.device import DeviceResponse
from app.services.device_service import DeviceService

router = APIRouter()


def _get_service(redis: Redis = Depends(get_redis)) -> DeviceService:
    return DeviceService(redis)


@router.get("", response_model=list[DeviceResponse])
async def list_devices(service: DeviceService = Depends(_get_service)):
    return await service.get_all()


@router.delete("/{device_id}/session", status_code=204)
async def release_session(
    device_id: str,
    service: DeviceService = Depends(_get_service),
):
    await service.release_session(device_id)
