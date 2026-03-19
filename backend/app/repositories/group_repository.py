from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import Group


class GroupRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self, type: str | None = None) -> list[Group]:
        query = select(Group).order_by(Group.name)
        if type:
            query = query.where(Group.type == type)
        result = await self._session.execute(query)
        return result.scalars().all()

    async def get_by_id(self, group_id: int) -> Group | None:
        result = await self._session.execute(select(Group).where(Group.id == group_id))
        return result.scalar_one_or_none()

    async def create(self, name: str, type: str) -> Group:
        group = Group(name=name, type=type)
        self._session.add(group)
        await self._session.flush()
        return group

    async def delete(self, group_id: int) -> bool:
        result = await self._session.execute(
            delete(Group).where(Group.id == group_id)
        )
        return result.rowcount > 0
