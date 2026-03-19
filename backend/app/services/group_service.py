from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.group_repository import GroupRepository
from app.schemas.group import GroupCreate, GroupResponse


class GroupService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = GroupRepository(session)
        self._session = session

    async def get_all(self, type: str | None = None) -> list[GroupResponse]:
        groups = await self._repo.get_all(type)
        return [GroupResponse.model_validate(g) for g in groups]

    async def create(self, data: GroupCreate) -> GroupResponse:
        group = await self._repo.create(name=data.name, type=data.type)
        await self._session.commit()
        return GroupResponse.model_validate(group)

    async def delete(self, group_id: int) -> None:
        deleted = await self._repo.delete(group_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Группа не найдена")
        await self._session.commit()
