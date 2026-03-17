import uuid
from datetime import datetime

from pydantic import BaseModel, model_validator


class DeviceLogCreate(BaseModel):
    event_type: str
    detail: str | None = None


class DeviceLogResponse(BaseModel):
    id: uuid.UUID
    serial: str
    event_type: str
    detail: str | None
    created_at: datetime
    # Enriched from devices table (not stored in device_logs)
    label: str | None = None
    owner_name: str | None = None

    model_config = {"from_attributes": True}


class DeviceCreate(BaseModel):
    serial: str
    label: str | None = None
    owner_name: str | None = None

    @model_validator(mode="after")
    def label_or_owner_required(self):
        if not self.label and not self.owner_name:
            raise ValueError("Необходимо указать название (label) или владельца")
        return self


class DeviceUpdate(BaseModel):
    label: str | None = None
    owner_name: str | None = None


class DeviceResponse(BaseModel):
    id: uuid.UUID
    serial: str
    label: str | None
    owner_name: str | None
    status: str           # online / offline  — physical ADB connection
    session_status: str   # active / inactive — admin access permission
    connected: bool       # someone is currently in a scrcpy session
    created_at: datetime

    model_config = {"from_attributes": True}


class UnregisteredDevice(BaseModel):
    serial: str
    status: str = "unregistered"


class DeviceListResponse(BaseModel):
    registered: list[DeviceResponse]
    unregistered: list[UnregisteredDevice]
