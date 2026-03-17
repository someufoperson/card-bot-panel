from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.redis import get_redis
from app.schemas.device import DeviceCreate, DeviceListResponse, DeviceLogCreate, DeviceLogResponse, DeviceResponse, DeviceUpdate
from app.services.device_service import DeviceService

router = APIRouter()


def _get_service(
    session: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis),
) -> DeviceService:
    return DeviceService(session, redis)


# ── Endpoints for device_support.py (static paths first) ─────────────────────

@router.get("/all-devices-online", response_model=list[str])
async def all_devices_online(service: DeviceService = Depends(_get_service)):
    """Returns list of registered device serials (for ADB polling daemon)."""
    return await service.get_all_serials()


@router.get("/device/status/{serial}")
async def device_status(serial: str, service: DeviceService = Depends(_get_service)):
    """Returns session_status / status_device / label for web-scrcpy gating."""
    return await service.get_status_for_scrcpy(serial)


@router.get("/device/{serial}")
async def device_label(serial: str, service: DeviceService = Depends(_get_service)):
    """Returns label for Telegram notification in web-scrcpy."""
    return await service.get_label(serial)


@router.patch("/update-status/online/{serial}/{status}", status_code=204)
async def update_online_status(
    serial: str,
    status: str,
    service: DeviceService = Depends(_get_service),
):
    await service.update_online_status(serial, status)


@router.patch("/update-status/connect/{serial}/{status}", status_code=204)
async def update_connected(
    serial: str,
    status: str,
    service: DeviceService = Depends(_get_service),
):
    """Called by host_server/app.py: status = 'connect' | 'disconnect'"""
    await service.update_connected(serial, status)


@router.patch("/access/all/{status}", status_code=204)
async def set_access_all(
    status: str,
    service: DeviceService = Depends(_get_service),
):
    """Bulk set access for all devices: status = 'active' | 'inactive'"""
    await service.set_access_all(status)


@router.patch("/{serial}/access/{status}", status_code=204)
async def set_access(
    serial: str,
    status: str,
    service: DeviceService = Depends(_get_service),
):
    """Admin toggles access permission: status = 'active' | 'inactive'"""
    await service.set_access(serial, status)


# ── CRUD ──────────────────────────────────────────────────────────────────────

@router.get("", response_model=DeviceListResponse)
async def list_devices(service: DeviceService = Depends(_get_service)):
    return await service.get_all()


@router.post("", response_model=DeviceResponse, status_code=201)
async def create_device(
    data: DeviceCreate,
    service: DeviceService = Depends(_get_service),
):
    return await service.create(data)


@router.patch("/{serial}", response_model=DeviceResponse)
async def update_device(
    serial: str,
    data: DeviceUpdate,
    service: DeviceService = Depends(_get_service),
):
    return await service.update(serial, data)


@router.delete("/{serial}", status_code=204)
async def delete_device(serial: str, service: DeviceService = Depends(_get_service)):
    await service.delete(serial)


@router.delete("/{serial}/session", status_code=204)
async def release_session(serial: str, service: DeviceService = Depends(_get_service)):
    await service.release_session(serial)


@router.get("/logs", response_model=list[DeviceLogResponse])
async def get_all_device_logs(service: DeviceService = Depends(_get_service)):
    return await service.get_all_logs()


@router.get("/{serial}/logs", response_model=list[DeviceLogResponse])
async def get_device_logs(serial: str, service: DeviceService = Depends(_get_service)):
    return await service.get_logs(serial)


@router.post("/{serial}/logs", status_code=204)
async def create_device_log(
    serial: str,
    data: DeviceLogCreate,
    service: DeviceService = Depends(_get_service),
):
    await service.create_log(serial, data)
