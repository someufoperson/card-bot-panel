from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.schemas.group import GroupCreate, GroupResponse
from app.services.group_service import GroupService

router = APIRouter()


def _get_service(session: AsyncSession = Depends(get_db_session)) -> GroupService:
    return GroupService(session)


@router.get("", response_model=list[GroupResponse])
async def list_groups(
    type: str | None = Query(None),
    service: GroupService = Depends(_get_service),
):
    return await service.get_all(type)


@router.post("", response_model=GroupResponse, status_code=201)
async def create_group(
    data: GroupCreate,
    service: GroupService = Depends(_get_service),
):
    return await service.create(data)


@router.delete("/{group_id}", status_code=204)
async def delete_group(
    group_id: int,
    service: GroupService = Depends(_get_service),
):
    await service.delete(group_id)
