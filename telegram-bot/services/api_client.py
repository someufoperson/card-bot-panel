import logging

import httpx

from config import settings

logger = logging.getLogger(__name__)

_BASE = settings.fastapi_url


async def create_card(card_data: dict) -> dict:
    """POST /api/v1/cards — создаёт карту в панели."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(f"{_BASE}/api/v1/cards", json=card_data)
        if resp.is_error:
            logger.error("create_card failed %s: %s", resp.status_code, resp.text)
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


async def get_donor_chat_ids() -> set[str]:
    """GET /api/v1/groups?type=donor — возвращает множество chat_id групп-доноров."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{_BASE}/api/v1/groups", params={"type": "donor"})
            resp.raise_for_status()
            return {g["name"] for g in resp.json()}
    except Exception as exc:
        logger.warning("Не удалось получить группы-доноры: %s", exc)
        return set()


async def save_pending(message_id: int, user_id: int, data: dict) -> None:
    """POST /api/v1/pending-cards — сохраняет ожидающую карту в БД."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{_BASE}/api/v1/pending-cards",
            json={"message_id": message_id, "user_id": user_id, "data": data},
        )
        resp.raise_for_status()


async def get_pending(message_id: int) -> dict | None:
    """GET /api/v1/pending-cards/{message_id} — получает данные карты по id сообщения."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(f"{_BASE}/api/v1/pending-cards/{message_id}")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()["data"]


async def delete_pending(message_id: int) -> None:
    """DELETE /api/v1/pending-cards/{message_id} — удаляет запись после подтверждения/отмены."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.delete(f"{_BASE}/api/v1/pending-cards/{message_id}")
        resp.raise_for_status()
