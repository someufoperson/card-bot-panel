from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.log_handler import push_log
from app.core.security import _decode

_ONLINE_TTL = 5 * 60  # 5 минут
_SKIP_PATHS = {"/health", "/api/v1/events"}


class ActivityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if any(request.url.path.startswith(p) for p in _SKIP_PATHS):
            return response

        session = request.cookies.get("session")
        if not session:
            return response

        payload = _decode(session)
        if not payload or payload.get("role") != "user":
            return response

        username = payload.get("sub")
        if not username:
            return response

        try:
            from app.core.redis import get_redis
            redis = await get_redis()
            key = f"panel:online:{username}"
            was_online = await redis.exists(key)
            await redis.setex(key, _ONLINE_TTL, "1")

            if not was_online:
                ip = request.headers.get("X-Real-IP") or request.client.host
                await push_log("INFO", f"Пользователь {username} онлайн (IP: {ip})")
        except Exception:
            pass

        return response
