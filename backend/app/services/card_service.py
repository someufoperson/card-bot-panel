import uuid

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card import Card
from app.repositories.card_repository import CardRepository
from app.schemas.card import CardCreate, CardListResponse, CardResponse, CardUpdate


def _to_response(card: Card) -> CardResponse:
    return CardResponse(
        id=card.id,
        full_name=card.full_name,
        bank=card.bank,
        card_number=card.card_number,
        card_last4=card.card_last4,
        phone_number=card.phone_number,
        purchase_date=card.purchase_date,
        group_name=card.group_name,
        created_at=card.created_at,
    )


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
    ) -> CardListResponse:
        cards, total = await self._repo.get_all(search, bank, group, page, limit)
        return CardListResponse(
            items=[_to_response(c) for c in cards],
            total=total,
            page=page,
            limit=limit,
        )

    async def get_by_id(self, card_id: uuid.UUID) -> CardResponse:
        card = await self._repo.get_by_id(card_id)
        if card is None:
            raise HTTPException(status_code=404, detail="Карта не найдена")
        return _to_response(card)

    async def create(self, data: CardCreate) -> CardResponse:
        card = Card(
            full_name=data.full_name,
            bank=data.bank,
            card_number=data.card_number,
            card_last4=data.card_number[-4:],
            phone_number=data.phone_number,
            purchase_date=data.purchase_date,
            group_name=data.group_name,
        )
        card = await self._repo.insert(card)
        await self._session.commit()
        return _to_response(card)

    async def update(self, card_id: uuid.UUID, data: CardUpdate) -> CardResponse:
        card = await self._repo.get_by_id(card_id)
        if card is None:
            raise HTTPException(status_code=404, detail="Карта не найдена")

        updates = data.model_dump(exclude_none=True)
        if "card_number" in updates:
            updates["card_last4"] = updates["card_number"][-4:]

        card = await self._repo.update(card, updates)
        await self._session.commit()
        return _to_response(card)

    async def delete(self, card_id: uuid.UUID) -> None:
        card = await self._repo.get_by_id(card_id)
        if card is None:
            raise HTTPException(status_code=404, detail="Карта не найдена")
        await self._repo.delete(card)
        await self._session.commit()
