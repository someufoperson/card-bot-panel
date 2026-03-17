import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.broadcaster import broadcaster
from app.models.card import Card
from app.models.card_block import CardBlock
from app.models.device import Device
from app.repositories.card_repository import CardRepository
from app.schemas.card import (
    CardBlockResponse,
    CardCreate,
    CardDeviceInfo,
    CardListResponse,
    CardResponse,
    CardUpdate,
)


def _to_response(card: Card, block: CardBlock | None = None, device: Device | None = None) -> CardResponse:
    return CardResponse(
        id=card.id,
        full_name=card.full_name,
        bank=card.bank,
        card_number=card.card_number,
        card_last4=card.card_last4,
        phone_number=card.phone_number,
        device_id=card.device_id,
        device=CardDeviceInfo.model_validate(device) if device else None,
        purchase_date=card.purchase_date,
        pickup_date=card.pickup_date,
        group_name=card.group_name,
        balance=card.balance,
        monthly_turnover=card.monthly_turnover,
        responsible_user=card.responsible_user,
        folder_link=card.folder_link,
        comment=card.comment,
        active_block=CardBlockResponse.model_validate(block) if block else None,
        created_at=card.created_at,
    )


async def _fetch_devices_by_ids(session: AsyncSession, ids: list[uuid.UUID]) -> dict[uuid.UUID, Device]:
    if not ids:
        return {}
    result = await session.execute(select(Device).where(Device.id.in_(ids)))
    return {d.id: d for d in result.scalars().all()}


class CardService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = CardRepository(session)
        self._session = session

    async def get_all(
        self,
        search: str | None,
        bank: str | None,
        group: str | None,
        page: int,
        limit: int,
        user: str | None = None,
    ) -> CardListResponse:
        cards, total = await self._repo.get_all(search, bank, group, user, page, limit)
        card_ids = [c.id for c in cards]
        active_blocks = await self._repo.get_active_blocks_for_cards(card_ids)
        device_ids = list({c.device_id for c in cards if c.device_id})
        devices = await _fetch_devices_by_ids(self._session, device_ids)
        return CardListResponse(
            items=[_to_response(c, active_blocks.get(c.id), devices.get(c.device_id)) for c in cards],
            total=total,
            page=page,
            limit=limit,
        )

    async def get_by_id(self, card_id: uuid.UUID) -> CardResponse:
        card = await self._repo.get_by_id(card_id)
        if card is None:
            raise HTTPException(status_code=404, detail="Карта не найдена")
        block = await self._repo.get_active_block(card_id)
        devices = await _fetch_devices_by_ids(self._session, [card.device_id] if card.device_id else [])
        return _to_response(card, block, devices.get(card.device_id))

    async def create(self, data: CardCreate) -> CardResponse:
        card = Card(
            full_name=data.full_name,
            bank=data.bank,
            card_number=data.card_number,
            card_last4=data.card_number[-4:],
            phone_number=data.phone_number,
            device_id=data.device_id,
            purchase_date=data.purchase_date,
            pickup_date=data.pickup_date,
            group_name=data.group_name,
            balance=data.balance,
            monthly_turnover=data.monthly_turnover,
            responsible_user=data.responsible_user,
            folder_link=data.folder_link,
            comment=data.comment,
        )
        card = await self._repo.insert(card)
        await self._session.commit()
        await broadcaster.publish("cards_updated")
        devices = await _fetch_devices_by_ids(self._session, [card.device_id] if card.device_id else [])
        return _to_response(card, device=devices.get(card.device_id))

    async def update(self, card_id: uuid.UUID, data: CardUpdate) -> CardResponse:
        card = await self._repo.get_by_id(card_id)
        if card is None:
            raise HTTPException(status_code=404, detail="Карта не найдена")

        updates = data.model_dump(exclude_none=True)
        # Allow explicitly clearing nullable fields
        clearable = {
            "device_id", "bank", "phone_number", "group_name", "responsible_user",
            "folder_link", "comment", "purchase_date", "pickup_date",
        }
        for field in clearable:
            if field in data.model_fields_set and getattr(data, field) is None:
                updates[field] = None
        if "card_number" in updates:
            updates["card_last4"] = updates["card_number"][-4:]

        card = await self._repo.update(card, updates)
        await self._session.commit()
        await broadcaster.publish("cards_updated")
        block = await self._repo.get_active_block(card_id)
        devices = await _fetch_devices_by_ids(self._session, [card.device_id] if card.device_id else [])
        return _to_response(card, block, devices.get(card.device_id))

    async def get_names(self) -> list[str]:
        return await self._repo.get_distinct_names()

    async def delete(self, card_id: uuid.UUID) -> None:
        card = await self._repo.get_by_id(card_id)
        if card is None:
            raise HTTPException(status_code=404, detail="Карта не найдена")
        await self._repo.delete(card)
        await self._session.commit()
        await broadcaster.publish("cards_updated")

    # ── Block endpoints ────────────────────────────────────────────────────────

    async def add_block(self, card_id: uuid.UUID, blocked_at: datetime | None = None) -> CardBlockResponse:
        card = await self._repo.get_by_id(card_id)
        if card is None:
            raise HTTPException(status_code=404, detail="Карта не найдена")
        existing = await self._repo.get_active_block(card_id)
        if existing:
            raise HTTPException(status_code=409, detail="Карта уже заблокирована")
        block = CardBlock(card_id=card_id, blocked_at=blocked_at or datetime.now(timezone.utc))
        block = await self._repo.insert_block(block)
        await self._session.commit()
        await broadcaster.publish("cards_updated")
        return CardBlockResponse.model_validate(block)

    async def remove_block(self, card_id: uuid.UUID, unblocked_at: datetime | None = None) -> CardBlockResponse:
        card = await self._repo.get_by_id(card_id)
        if card is None:
            raise HTTPException(status_code=404, detail="Карта не найдена")
        block = await self._repo.close_block(card_id, unblocked_at)
        if block is None:
            raise HTTPException(status_code=404, detail="Активная блокировка не найдена")
        await self._session.commit()
        await broadcaster.publish("cards_updated")
        return CardBlockResponse.model_validate(block)

    async def get_blocks(self, card_id: uuid.UUID) -> list[CardBlockResponse]:
        card = await self._repo.get_by_id(card_id)
        if card is None:
            raise HTTPException(status_code=404, detail="Карта не найдена")
        blocks = await self._repo.get_all_blocks(card_id)
        return [CardBlockResponse.model_validate(b) for b in blocks]
