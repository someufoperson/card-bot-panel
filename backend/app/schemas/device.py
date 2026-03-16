from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class DeviceStatus(str, Enum):
    online = "online"
    offline = "offline"
    busy = "busy"


class DeviceResponse(BaseModel):
    device_id: str
    model: str | None
    status: DeviceStatus
    session_started: datetime | None
    session_id: str | None
