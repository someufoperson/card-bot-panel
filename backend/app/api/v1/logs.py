import json

from fastapi import APIRouter, Depends, Query

from app.core.redis import get_redis
from app.core.security import require_role

router = APIRouter()


@router.get("")
async def get_logs(
    source: str | None = Query(None, description="backend | bot | flask"),
    payload: dict = Depends(require_role("dev")),
):
    redis = await get_redis()
    raw = await redis.lrange("panel:logs", -500, -1)
    entries = []
    for item in raw:
        try:
            entry = json.loads(item)
            if source and entry.get("s") != source:
                continue
            entries.append(entry)
        except Exception:
            pass
    return entries
