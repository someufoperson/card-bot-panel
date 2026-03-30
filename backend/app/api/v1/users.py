import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.security import require_role
from app.models.user import User

router = APIRouter()

VALID_ROLES = {"admin", "dev", "user"}


class CreateUserRequest(BaseModel):
    username: str
    role: str = "user"


class UserOut(BaseModel):
    id: uuid.UUID
    username: str
    role: str
    must_set_password: bool

    model_config = {"from_attributes": True}


@router.get("/usernames", response_model=list[str])
async def list_usernames(
    payload: dict = Depends(require_role("admin", "dev")),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(select(User.username).order_by(User.username))
    return result.scalars().all()


@router.get("/", response_model=list[UserOut])
async def list_users(
    payload: dict = Depends(require_role("admin", "dev")),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(select(User).order_by(User.created_at))
    return result.scalars().all()


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: CreateUserRequest,
    payload: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db_session),
):
    if body.role not in VALID_ROLES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неверная роль")

    existing = await db.execute(select(User).where(User.username == body.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Пользователь уже существует")

    user = User(username=body.username, role=body.role, must_set_password=True)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    payload: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    # Prevent deleting yourself
    if user.username == payload.get("sub"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нельзя удалить себя")
    await db.delete(user)
    await db.commit()


@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: uuid.UUID,
    payload: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    user.must_set_password = True
    user.password_hash = None
    await db.commit()
    return {"ok": True}
