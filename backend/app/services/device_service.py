import json
import logging
from datetime import datetime

import httpx
from redis.asyncio import Redis

from app.schemas.device import DeviceResponse, DeviceStatus

logger = logging.getLogger(__name__)

_SCRCPY_API_URL = "http://host.docker.internal:5000/api/devices"
_SESSION_KEY_PREFIX = "session:lock:"


class DeviceService:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def get_all(self) -> list[DeviceResponse]:
        raw_devices = await self._fetch_scrcpy_devices()
        return [await self._build_response(d) for d in raw_devices]

    async def release_session(self, device_id: str) -> None:
        await self._redis.delete(f"{_SESSION_KEY_PREFIX}{device_id}")

    async def _fetch_scrcpy_devices(self) -> list[dict]:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(_SCRCPY_API_URL)
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            logger.warning("web-scrcpy недоступен: %s", exc)
            return await self._devices_from_redis()

    async def _devices_from_redis(self) -> list[dict]:
        """Fallback: собираем устройства только из Redis-сессий."""
        keys = await self._redis.keys(f"{_SESSION_KEY_PREFIX}*")
        devices = []
        for key in keys:
            device_id = key.removeprefix(_SESSION_KEY_PREFIX)
            devices.append({"device_id": device_id, "model": None, "adb_status": "unknown"})
        return devices

    async def _build_response(self, raw: dict) -> DeviceResponse:
        device_id = raw.get("device_id", raw.get("id", ""))
        model = raw.get("model")

        session_data = await self._redis.get(f"{_SESSION_KEY_PREFIX}{device_id}")
        if session_data:
            session = json.loads(session_data)
            status = DeviceStatus.busy
            session_started = datetime.fromisoformat(session["connected_at"])
            session_id = session["session_id"]
        else:
            adb_status = raw.get("adb_status", "online")
            status = DeviceStatus.online if adb_status == "online" else DeviceStatus.offline
            session_started = None
            session_id = None

        return DeviceResponse(
            device_id=device_id,
            model=model,
            status=status,
            session_started=session_started,
            session_id=session_id,
        )
