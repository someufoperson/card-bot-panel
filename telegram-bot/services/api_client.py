import logging

import httpx

from config import settings

logger = logging.getLogger(__name__)

_BASE = settings.fastapi_url


async def create_card(card_data: dict) -> dict:
    """POST /api/v1/cards — создаёт карту в панели."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(f"{_BASE}/api/v1/cards", json=card_data)
        resp.raise_for_status()
        return resp.json()


async def get_setting(key: str) -> str | None:
    """GET /api/v1/settings/{key} — получает значение настройки."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{_BASE}/api/v1/settings/{key}")
            if resp.status_code == 200:
                return resp.json()["value"]
    except Exception as exc:
        logger.warning("Не удалось получить настройку %s: %s", key, exc)
    return None
