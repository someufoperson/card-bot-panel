import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.setting import Setting


class SettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> list[Setting]:
        result = await self._session.execute(select(Setting).order_by(Setting.key))
        return result.scalars().all()

    async def get_by_key(self, key: str) -> Setting | None:
        result = await self._session.execute(select(Setting).where(Setting.key == key))
        return result.scalar_one_or_none()

    async def upsert(self, key: str, value: str) -> Setting:
        stmt = (
            insert(Setting)
            .values(key=key, value=value)
            .on_conflict_do_update(
                index_elements=["key"],
                set_={"value": value, "updated_at": sa.text("NOW()")},
            )
            .returning(Setting)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.scalar_one()

    async def bulk_upsert(self, data: dict[str, str]) -> list[Setting]:
        results = []
        for key, value in data.items():
            setting = await self.upsert(key, value)
            results.append(setting)
        return results
