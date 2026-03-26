from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Cookie, HTTPException, status
from jose import JWTError, jwt

from app.core.config import settings

_ALGORITHM = "HS256"


def create_access_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_expire_days)
    return jwt.encode({"sub": username, "exp": expire}, settings.jwt_secret, algorithm=_ALGORITHM)


def _decode(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[_ALGORITHM])
    except JWTError:
        return None


def verify_session(session: Optional[str] = Cookie(default=None)) -> dict:
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Требуется авторизация")
    payload = _decode(session)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Сессия истекла или недействительна")
    return payload
