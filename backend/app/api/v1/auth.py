from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db_session
from app.core.log_handler import push_log
from app.core.security import create_access_token, pwd_context, verify_session
from app.models.user import User

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str | None = None


class SetupPasswordRequest(BaseModel):
    username: str
    new_password: str


@router.post("/login")
async def login(
    body: LoginRequest,
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный логин или пароль")

    if user.must_set_password:
        return {"ok": False, "must_set_password": True}

    if not body.password or not user.password_hash or not pwd_context.verify(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный логин или пароль")

    token = create_access_token(user.username, user.role)
    response.set_cookie(
        key="session",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=settings.jwt_expire_days * 86400,
    )
    if user.role == "user":
        ip = request.headers.get("X-Real-IP") or request.client.host
        await push_log("INFO", f"Вход пользователя {user.username} с IP {ip}")
    return {"ok": True}


@router.post("/setup-password")
async def setup_password(
    body: SetupPasswordRequest,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()

    if not user or not user.must_set_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Недопустимая операция")

    if len(body.new_password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пароль должен быть не менее 6 символов")

    user.password_hash = pwd_context.hash(body.new_password)
    user.must_set_password = False
    await db.commit()

    token = create_access_token(user.username, user.role)
    response.set_cookie(
        key="session",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=settings.jwt_expire_days * 86400,
    )
    return {"ok": True}


@router.post("/logout")
async def logout(response: Response, request: Request):
    session = request.cookies.get("session")
    if session:
        from app.core.security import _decode
        payload = _decode(session)
        if payload and payload.get("role") == "user":
            username = payload.get("sub")
            await push_log("INFO", f"Пользователь {username} вышел из системы")
            try:
                from app.core.redis import get_redis
                redis = await get_redis()
                await redis.delete(f"panel:online:{username}")
            except Exception:
                pass
    response.delete_cookie("session", samesite="lax")
    return {"ok": True}


@router.get("/me")
async def me(payload: dict = Depends(verify_session)):
    return {"username": payload.get("sub"), "role": payload.get("role")}
