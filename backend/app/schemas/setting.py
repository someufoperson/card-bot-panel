from datetime import datetime

from pydantic import BaseModel


class SettingResponse(BaseModel):
    key: str
    value: str
    updated_at: datetime

    model_config = {"from_attributes": True}


class SettingUpdate(BaseModel):
    value: str


class SettingBulkUpdate(BaseModel):
    settings: dict[str, str]
