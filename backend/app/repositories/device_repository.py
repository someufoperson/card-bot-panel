import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device
from app.models.device_log import DeviceLog


class DeviceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> list[Device]:
        result = await self._session.execute(select(Device).order_by(Device.created_at))
        return list(result.scalars().all())

    async def get_by_serial(self, serial: str) -> Device | None:
        result = await self._session.execute(
            select(Device).where(Device.serial == serial)
        )
        return result.scalar_one_or_none()

    async def get_all_serials(self) -> list[str]:
        result = await self._session.execute(select(Device.serial))
        return list(result.scalars().all())

    async def insert(self, device: Device) -> Device:
        self._session.add(device)
        await self._session.flush()
        await self._session.refresh(device)
        return device

    async def update(self, device: Device, updates: dict) -> Device:
        for k, v in updates.items():
            setattr(device, k, v)
        await self._session.flush()
        await self._session.refresh(device)
        return device

    async def delete(self, device: Device) -> None:
        await self._session.delete(device)
        await self._session.flush()

    async def update_status(self, serial: str, status: str) -> None:
        await self._session.execute(
            update(Device).where(Device.serial == serial).values(status=status)
        )

    async def update_session_status(self, serial: str, session_status: str) -> None:
        await self._session.execute(
            update(Device)
            .where(Device.serial == serial)
            .values(session_status=session_status)
        )

    async def update_connected(self, serial: str, connected: bool) -> None:
        await self._session.execute(
            update(Device)
            .where(Device.serial == serial)
            .values(connected=connected)
        )

    async def update_all_session_status(self, session_status: str) -> None:
        await self._session.execute(
            update(Device).values(session_status=session_status)
        )

    # ── Logs ──────────────────────────────────────────────────────────────────

    def log_event(self, serial: str, event_type: str, detail: str | None = None) -> None:
        """Append a log row (no flush — caller commits)."""
        self._session.add(DeviceLog(serial=serial, event_type=event_type, detail=detail))

    async def get_logs(self, serial: str, limit: int = 200) -> list[DeviceLog]:
        result = await self._session.execute(
            select(DeviceLog)
            .where(DeviceLog.serial == serial)
            .order_by(DeviceLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_all_logs(self, limit: int = 500) -> list[DeviceLog]:
        result = await self._session.execute(
            select(DeviceLog)
            .order_by(DeviceLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
