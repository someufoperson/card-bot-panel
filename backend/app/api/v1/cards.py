import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.schemas.card import CardCreate, CardListResponse, CardResponse, CardUpdate
from app.services.card_service import CardService

router = APIRouter()


def _get_service(session: AsyncSession = Depends(get_db_session)) -> CardService:
    return CardService(session)


@router.get("", response_model=CardListResponse)
async def list_cards(
    search: str | None = Query(None),
    bank: str | None = Query(None),
    group: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    service: CardService = Depends(_get_service),
):
    return await service.get_all(search, bank, group, page, limit)


@router.post("", response_model=CardResponse, status_code=201)
async def create_card(
    data: CardCreate,
    service: CardService = Depends(_get_service),
):
    return await service.create(data)


@router.get("/{card_id}", response_model=CardResponse)
async def get_card(
    card_id: uuid.UUID,
    service: CardService = Depends(_get_service),
):
    return await service.get_by_id(card_id)


@router.put("/{card_id}", response_model=CardResponse)
async def update_card(
    card_id: uuid.UUID,
    data: CardUpdate,
    service: CardService = Depends(_get_service),
):
    return await service.update(card_id, data)


@router.delete("/{card_id}", status_code=204)
async def delete_card(
    card_id: uuid.UUID,
    service: CardService = Depends(_get_service),
):
    await service.delete(card_id)
