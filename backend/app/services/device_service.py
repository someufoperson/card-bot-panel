import logging
import uuid

from fastapi import HTTPException
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.broadcaster import broadcaster
from app.models.device import Device
from app.repositories.device_repository import DeviceRepository
from app.schemas.device import (
    DeviceCreate,
    DeviceListResponse,
    DeviceLogCreate,
    DeviceLogResponse,
    DeviceResponse,
    DeviceUpdate,
    UnregisteredDevice,
)

logger = logging.getLogger(__name__)

_UNREGISTERED_KEY = "devices"          # Redis SET — serials visible in ADB but not registered
_SESSION_PREFIX   = "session:lock:"    # Redis key prefix for session locks

# Maps raw status values from host_server to stored event_type labels
_CONNECT_EVENT = {
    "connect":    "connected",
    "disconnect": "disconnected",
    "timeout":    "timeout",
}


class DeviceService:
    def __init__(self, session: AsyncSession, redis: Redis) -> None:
        self._repo  = DeviceRepository(session)
        self._session = session
        self._redis = redis

    # ── List ─────────────────────────────────────────────────────────────────

    async def get_all(self) -> DeviceListResponse:
        devices = await self._repo.get_all()
        registered = [self._to_response(d) for d in devices]

        known = {d.serial for d in devices}
        raw = await self._redis.smembers(_UNREGISTERED_KEY)
        unregistered = [
            UnregisteredDevice(serial=s.decode() if isinstance(s, bytes) else s)
            for s in raw
            if (s.decode() if isinstance(s, bytes) else s) not in known
        ]

        return DeviceListResponse(registered=registered, unregistered=unregistered)

    async def get_all_serials(self) -> list[str]:
        return await self._repo.get_all_serials()

    # ── CRUD ──────────────────────────────────────────────────────────────────

    async def create(self, data: DeviceCreate) -> DeviceResponse:
        if await self._repo.get_by_serial(data.serial):
            raise HTTPException(status_code=409, detail="Устройство уже зарегистрировано")
        is_online = bool(await self._redis.sismember(_UNREGISTERED_KEY, data.serial))
        device = Device(
            serial=data.serial,
            label=data.label,
            owner_name=data.owner_name,
            status="online" if is_online else "offline",
        )
        device = await self._repo.insert(device)
        await self._session.commit()
        await self._redis.srem(_UNREGISTERED_KEY, data.serial)
        await broadcaster.publish("devices_updated")
        return self._to_response(device)

    async def update(self, serial: str, data: DeviceUpdate) -> DeviceResponse:
        device = await self._repo.get_by_serial(serial)
        if device is None:
            raise HTTPException(status_code=404, detail="Устройство не найдено")

        updates = data.model_dump(exclude_unset=True)
        final_label      = updates.get("label",      device.label)
        final_owner_name = updates.get("owner_name", device.owner_name)
        if not final_label and not final_owner_name:
            raise HTTPException(
                status_code=422,
                detail="Необходимо указать название (label) или владельца",
            )

        device = await self._repo.update(device, updates)
        await self._session.commit()
        await broadcaster.publish("devices_updated")
        return self._to_response(device)

    async def delete(self, serial: str) -> None:
        device = await self._repo.get_by_serial(serial)
        if device is None:
            raise HTTPException(status_code=404, detail="Устройство не найдено")
        await self._repo.delete(device)
        await self._session.commit()
        await self._redis.sadd(_UNREGISTERED_KEY, serial)
        await broadcaster.publish("devices_updated")

    # ── Status updates (called by device_support.py and host_server/app.py) ──

    async def update_online_status(self, serial: str, status: str) -> None:
        """status = 'online' | 'offline'. Logs and emits SSE only when status actually changes."""
        device = await self._repo.get_by_serial(serial)
        if device is None:
            return
        await self._repo.update_status(serial, status)
        if device.status != status:
            self._repo.log_event(serial, status)  # "online" or "offline"
            await self._session.commit()
            await broadcaster.publish("devices_updated")
        else:
            await self._session.commit()

    async def set_access(self, serial: str, status: str) -> None:
        """Admin toggles access permission: status = 'active' | 'inactive'."""
        device = await self._repo.get_by_serial(serial)
        if device is None:
            raise HTTPException(status_code=404, detail="Устройство не найдено")
        await self._repo.update_session_status(serial, status)
        await self._session.commit()
        await broadcaster.publish("devices_updated")

    async def set_access_all(self, status: str) -> None:
        """Bulk set session_status for all registered devices."""
        await self._repo.update_all_session_status(status)
        await self._session.commit()
        await broadcaster.publish("devices_updated")

    async def update_connected(self, serial: str, raw_status: str) -> None:
        """Called by host_server/app.py: raw_status = 'connect' | 'disconnect' | 'timeout'."""
        connected = raw_status == "connect"
        await self._repo.update_connected(serial, connected)
        event_type = _CONNECT_EVENT.get(raw_status, raw_status)
        self._repo.log_event(serial, event_type)
        await self._session.commit()
        await broadcaster.publish("devices_updated")

    async def release_session(self, serial: str) -> None:
        await self._redis.delete(f"{_SESSION_PREFIX}{serial}")
        await self._repo.update_connected(serial, False)
        await self._session.commit()

    # ── Logs ─────────────────────────────────────────────────────────────────

    async def get_all_logs(self) -> list[DeviceLogResponse]:
        logs = await self._repo.get_all_logs()
        devices = await self._repo.get_all()
        device_map = {d.serial: d for d in devices}
        result = []
        for log in logs:
            resp = DeviceLogResponse.model_validate(log)
            dev = device_map.get(log.serial)
            if dev:
                resp.label = dev.label
                resp.owner_name = dev.owner_name
            result.append(resp)
        return result

    async def get_logs(self, serial: str) -> list[DeviceLogResponse]:
        device = await self._repo.get_by_serial(serial)
        if device is None:
            raise HTTPException(status_code=404, detail="Устройство не найдено")
        logs = await self._repo.get_logs(serial)
        return [DeviceLogResponse.model_validate(log) for log in logs]

    async def create_log(self, serial: str, data: DeviceLogCreate) -> None:
        """Called externally (e.g. host_server) to push a custom log entry."""
        self._repo.log_event(serial, data.event_type, data.detail)
        await self._session.commit()
        await broadcaster.publish("devices_updated")

    # ── Endpoints consumed by host_server/app.py ──────────────────────────────

    async def get_status_for_scrcpy(self, serial: str) -> dict:
        device = await self._repo.get_by_serial(serial)
        if device is None:
            raise HTTPException(status_code=404, detail="Устройство не найдено")
        return {
            "session_status": "ACTIVE" if device.session_status == "active" else "INACTIVE",
            "status_device":  "ONLINE" if device.status == "online" else "OFFLINE",
            "label": device.label or device.owner_name or device.serial,
        }

    async def get_label(self, serial: str) -> dict:
        device = await self._repo.get_by_serial(serial)
        if device is None:
            raise HTTPException(status_code=404, detail="Устройство не найдено")
        return {"label": device.label or device.owner_name or device.serial}

    # ── Internal ──────────────────────────────────────────────────────────────

    def _to_response(self, device: Device) -> DeviceResponse:
        return DeviceResponse(
            id=device.id,
            serial=device.serial,
            label=device.label,
            owner_name=device.owner_name,
            status=device.status,
            session_status=device.session_status,
            connected=device.connected,
            created_at=device.created_at,
        )
