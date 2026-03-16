import json
import logging
import uuid
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_SESSION_KEY_PREFIX = "session:lock:"
_DEFAULT_TIMEOUT = 10 * 60  # 10 минут


class SessionManager:
    """
    Управляет эксклюзивными Redis-сессиями для устройств.
    При недоступности Redis автоматически переключается на in-memory dict с предупреждением.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/0", timeout_seconds: int = _DEFAULT_TIMEOUT):
        self._timeout = timeout_seconds
        self._fallback: dict[str, str] = {}
        self._redis = None
        self._use_redis = False

        try:
            import redis as redis_lib
            client = redis_lib.from_url(redis_url, decode_responses=True, socket_connect_timeout=2)
            client.ping()
            self._redis = client
            self._use_redis = True
            logger.info("SessionManager: Redis подключён (%s)", redis_url)
        except Exception as exc:
            logger.warning("SessionManager: Redis недоступен (%s), используем in-memory хранилище", exc)

    def set_timeout(self, seconds: int) -> None:
        self._timeout = seconds

    def acquire(self, device_id: str) -> str:
        """Создать сессию. Возвращает session_id."""
        session_id = str(uuid.uuid4())
        data = json.dumps({
            "session_id": session_id,
            "connected_at": datetime.now(timezone.utc).isoformat(),
        })
        key = _SESSION_KEY_PREFIX + device_id

        if self._use_redis:
            self._redis.setex(key, self._timeout, data)
        else:
            self._fallback[key] = data

        return session_id

    def release(self, device_id: str) -> None:
        """Снять блокировку устройства."""
        key = _SESSION_KEY_PREFIX + device_id
        if self._use_redis:
            self._redis.delete(key)
        else:
            self._fallback.pop(key, None)

    def refresh(self, device_id: str) -> None:
        """Обновить TTL сессии (вызывается при активности пользователя)."""
        key = _SESSION_KEY_PREFIX + device_id
        if self._use_redis:
            self._redis.expire(key, self._timeout)

    def get_session(self, device_id: str) -> dict | None:
        """Вернуть данные активной сессии или None."""
        key = _SESSION_KEY_PREFIX + device_id
        if self._use_redis:
            raw = self._redis.get(key)
        else:
            raw = self._fallback.get(key)

        return json.loads(raw) if raw else None

    def is_locked(self, device_id: str) -> bool:
        return self.get_session(device_id) is not None
