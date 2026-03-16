import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card import Card


class CardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(
        self,
        search: str | None = None,
        bank: str | None = None,
        group: str | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> tuple[list[Card], int]:
        query = select(Card)

        if search:
            query = query.where(
                or_(
                    Card.full_name.ilike(f"%{search}%"),
                    Card.bank.ilike(f"%{search}%"),
                    Card.card_last4.ilike(f"%{search}%"),
                )
            )
        if bank:
            query = query.where(Card.bank == bank)
        if group:
            query = query.where(Card.group_name == group)

        total_result = await self._session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = total_result.scalar_one()

        query = query.order_by(Card.created_at.desc())
        query = query.offset((page - 1) * limit).limit(limit)

        result = await self._session.execute(query)
        return result.scalars().all(), total

    async def get_by_id(self, card_id: uuid.UUID) -> Card | None:
        result = await self._session.execute(select(Card).where(Card.id == card_id))
        return result.scalar_one_or_none()

    async def insert(self, card: Card) -> Card:
        self._session.add(card)
        await self._session.flush()
        await self._session.refresh(card)
        return card

    async def update(self, card: Card, data: dict) -> Card:
        for key, value in data.items():
            setattr(card, key, value)
        await self._session.flush()
        await self._session.refresh(card)
        return card

    async def delete(self, card: Card) -> None:
        await self._session.delete(card)
        await self._session.flush()
