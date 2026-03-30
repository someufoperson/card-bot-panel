import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models.pending_card import PendingCard

router = APIRouter()


class PendingCardSave(BaseModel):
    message_id: int
    user_id: int
    data: dict


@router.post("", status_code=201)
async def save_pending(
    body: PendingCardSave,
    session: AsyncSession = Depends(get_db_session),
):
    existing = await session.get(PendingCard, body.message_id)
    if existing:
        existing.data = body.data
    else:
        session.add(
            PendingCard(
                message_id=body.message_id,
                user_id=body.user_id,
                data=body.data,
            )
        )
    await session.commit()
    return {"ok": True}


@router.get("")
async def list_pending(session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(
        sa.select(PendingCard).order_by(PendingCard.created_at)
    )
    rows = result.scalars().all()
    return [
        {
            "message_id": r.message_id,
            "user_id": r.user_id,
            "data": r.data,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.get("/{message_id}")
async def get_pending(
    message_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    row = await session.get(PendingCard, message_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Not found")
    return {"data": row.data}


@router.delete("/{message_id}")
async def delete_pending(
    message_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    row = await session.get(PendingCard, message_id)
    if row:
        await session.delete(row)
        await session.commit()
    return {"ok": True}
