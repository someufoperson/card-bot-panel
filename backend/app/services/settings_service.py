import json

from fastapi import HTTPException
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.settings_repository import SettingsRepository
from app.schemas.setting import SettingResponse

_CACHE_TTL = 60
_CACHE_PREFIX = "settings:cache:"


class SettingsService:
    def __init__(self, session: AsyncSession, redis: Redis) -> None:
        self._repo = SettingsRepository(session)
        self._redis = redis
        self._session = session

    async def get_all(self) -> list[SettingResponse]:
        settings = await self._repo.get_all()
        return [SettingResponse.model_validate(s) for s in settings]

    async def get_by_key(self, key: str) -> SettingResponse:
        cache_key = f"{_CACHE_PREFIX}{key}"
        cached = await self._redis.get(cache_key)
        if cached:
            return SettingResponse(**json.loads(cached))

        setting = await self._repo.get_by_key(key)
        if setting is None:
            raise HTTPException(status_code=404, detail=f"Настройка '{key}' не найдена")

        response = SettingResponse.model_validate(setting)
        await self._redis.setex(cache_key, _CACHE_TTL, response.model_dump_json())
        return response

    async def update(self, key: str, value: str) -> SettingResponse:
        setting = await self._repo.upsert(key, value)
        await self._session.commit()
        await self._redis.delete(f"{_CACHE_PREFIX}{key}")
        return SettingResponse.model_validate(setting)

    async def bulk_update(self, data: dict[str, str]) -> list[SettingResponse]:
        settings = await self._repo.bulk_upsert(data)
        await self._session.commit()
        for key in data:
            await self._redis.delete(f"{_CACHE_PREFIX}{key}")
        return [SettingResponse.model_validate(s) for s in settings]
