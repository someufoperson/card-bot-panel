from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import Cookie, Depends, HTTPException, status
from jose import JWTError, jwt

from app.core.config import settings

_ALGORITHM = "HS256"


class _PwdContext:
    def hash(self, secret: str) -> str:
        return bcrypt.hashpw(secret[:72].encode(), bcrypt.gensalt()).decode()

    def verify(self, secret: str, hashed: str) -> bool:
        return bcrypt.checkpw(secret[:72].encode(), hashed.encode())


pwd_context = _PwdContext()


def create_access_token(username: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_expire_days)
    return jwt.encode(
        {"sub": username, "role": role, "exp": expire},
        settings.jwt_secret,
        algorithm=_ALGORITHM,
    )


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


def require_role(*roles: str):
    def dependency(payload: dict = Depends(verify_session)) -> dict:
        if payload.get("role") not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
        return payload
    return dependency
