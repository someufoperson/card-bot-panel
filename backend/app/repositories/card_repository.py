import uuid
from datetime import datetime, timezone

from sqlalchemy import distinct, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card import Card
from app.models.card_block import CardBlock


class CardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(
        self,
        search: str | None = None,
        bank: str | None = None,
        group: str | None = None,
        user: str | None = None,
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
        if user:
            query = query.where(Card.responsible_user == user)

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

    async def get_distinct_names(self) -> list[str]:
        result = await self._session.execute(
            select(distinct(Card.full_name)).order_by(Card.full_name)
        )
        return list(result.scalars().all())

    # ── Block methods ──────────────────────────────────────────────────────────

    async def get_active_block(self, card_id: uuid.UUID) -> CardBlock | None:
        result = await self._session.execute(
            select(CardBlock).where(
                CardBlock.card_id == card_id,
                CardBlock.unblocked_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_active_blocks_for_cards(
        self, card_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, CardBlock]:
        if not card_ids:
            return {}
        result = await self._session.execute(
            select(CardBlock).where(
                CardBlock.card_id.in_(card_ids),
                CardBlock.unblocked_at.is_(None),
            )
        )
        return {b.card_id: b for b in result.scalars().all()}

    async def get_all_blocks(self, card_id: uuid.UUID) -> list[CardBlock]:
        result = await self._session.execute(
            select(CardBlock)
            .where(CardBlock.card_id == card_id)
            .order_by(CardBlock.blocked_at.desc())
        )
        return list(result.scalars().all())

    async def insert_block(self, block: CardBlock) -> CardBlock:
        self._session.add(block)
        await self._session.flush()
        await self._session.refresh(block)
        return block

    async def close_block(self, card_id: uuid.UUID, unblocked_at: datetime | None = None) -> CardBlock | None:
        block = await self.get_active_block(card_id)
        if block:
            block.unblocked_at = unblocked_at or datetime.now(timezone.utc)
            await self._session.flush()
            await self._session.refresh(block)
        return block
