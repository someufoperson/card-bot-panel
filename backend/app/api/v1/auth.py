from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel

from app.core.config import settings
from app.core.security import create_access_token, verify_session

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
async def login(body: LoginRequest, response: Response):
    if body.username != settings.panel_username or body.password != settings.panel_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный логин или пароль")
    token = create_access_token(body.username)
    response.set_cookie(
        key="session",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=settings.jwt_expire_days * 86400,
    )
    return {"ok": True}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("session", samesite="lax")
    return {"ok": True}


@router.get("/me")
async def me(payload: dict = Depends(verify_session)):
    return {"username": payload.get("sub")}
