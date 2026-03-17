from datetime import datetime, timedelta, timezone

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models.pending_card import PendingCard

router = APIRouter()

_TTL_MINUTES = 30


class PendingCardSave(BaseModel):
    message_id: int
    user_id: int
    data: dict


@router.post("", status_code=201)
async def save_pending(
    body: PendingCardSave,
    session: AsyncSession = Depends(get_db_session),
):
    # Purge stale entries older than TTL
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=_TTL_MINUTES)
    await session.execute(
        sa.delete(PendingCard).where(PendingCard.created_at < cutoff)
    )

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
