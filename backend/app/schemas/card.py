import re
import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator


class CardBlockCreate(BaseModel):
    blocked_at: datetime | None = None


class CardUnblockCreate(BaseModel):
    unblocked_at: datetime | None = None


class CardBlockResponse(BaseModel):
    id: uuid.UUID
    card_id: uuid.UUID
    blocked_at: datetime
    unblocked_at: datetime | None

    model_config = {"from_attributes": True}


class CardDeviceInfo(BaseModel):
    id: uuid.UUID
    serial: str
    label: str | None
    owner_name: str | None

    model_config = {"from_attributes": True}


class CardCreate(BaseModel):
    full_name: str
    bank: str | None = None
    card_number: str
    phone_number: str | None = None
    device_id: uuid.UUID | None = None
    purchase_date: date | None = None
    pickup_date: date | None = None
    group_name: str | None = None
    balance: Decimal | None = None
    monthly_turnover: Decimal | None = None
    responsible_user: str | None = None
    folder_link: str | None = None
    comment: str | None = None

    @field_validator("responsible_user")
    @classmethod
    def normalize_username(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        return v if v.startswith("@") else f"@{v}"

    @field_validator("card_number")
    @classmethod
    def validate_card_number(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v)
        if len(digits) != 16:
            raise ValueError("Номер карты должен содержать 16 цифр")
        return digits

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not re.match(r"^\+7\d{10}$", v):
            raise ValueError("Телефон должен быть в формате +7XXXXXXXXXX")
        return v


class CardUpdate(BaseModel):
    full_name: str | None = None
    bank: str | None = None
    card_number: str | None = None
    phone_number: str | None = None
    device_id: uuid.UUID | None = None
    purchase_date: date | None = None
    pickup_date: date | None = None
    group_name: str | None = None
    balance: Decimal | None = None
    monthly_turnover: Decimal | None = None
    responsible_user: str | None = None
    folder_link: str | None = None
    comment: str | None = None

    @field_validator("responsible_user")
    @classmethod
    def normalize_username(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        return v if v.startswith("@") else f"@{v}"

    @field_validator("card_number")
    @classmethod
    def validate_card_number(cls, v: str | None) -> str | None:
        if v is None:
            return v
        digits = re.sub(r"\D", "", v)
        if len(digits) != 16:
            raise ValueError("Номер карты должен содержать 16 цифр")
        return digits

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not re.match(r"^\+7\d{10}$", v):
            raise ValueError("Телефон должен быть в формате +7XXXXXXXXXX")
        return v


class CardResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    bank: str | None
    card_number: str
    card_last4: str
    phone_number: str | None
    device_id: uuid.UUID | None
    device: CardDeviceInfo | None = None
    purchase_date: date | None
    pickup_date: date | None
    group_name: str | None
    balance: Decimal | None
    monthly_turnover: Decimal | None
    responsible_user: str | None
    folder_link: str | None
    comment: str | None
    active_block: CardBlockResponse | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CardListResponse(BaseModel):
    items: list[CardResponse]
    total: int
    page: int
    limit: int
