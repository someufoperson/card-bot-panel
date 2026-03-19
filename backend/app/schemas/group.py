from datetime import datetime
from typing import Literal

from pydantic import BaseModel

GroupType = Literal["donor", "issuance"]


class GroupCreate(BaseModel):
    name: str
    type: GroupType


class GroupResponse(BaseModel):
    id: int
    name: str
    type: str
    created_at: datetime

    model_config = {"from_attributes": True}
