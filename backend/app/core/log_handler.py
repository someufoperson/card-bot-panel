import json
import logging
from datetime import datetime, timezone

import redis as redis_sync

_LOG_KEY = "panel:logs"
_LOG_MAXLEN = 1000


class RedisLogHandler(logging.Handler):
    def __init__(self, redis_url: str, source: str):
        super().__init__()
        self._r = redis_sync.from_url(redis_url, decode_responses=True)
        self._source = source

    def emit(self, record: logging.LogRecord):
        try:
            entry = json.dumps({
                "t": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                "l": record.levelname,
                "s": self._source,
                "m": self.format(record),
            }, ensure_ascii=False)
            pipe = self._r.pipeline()
            pipe.rpush(_LOG_KEY, entry)
            pipe.ltrim(_LOG_KEY, -_LOG_MAXLEN, -1)
            pipe.execute()
        except Exception:
            pass


def setup_redis_logging(redis_url: str, source: str, level: int = logging.INFO) -> None:
    handler = RedisLogHandler(redis_url, source)
    handler.setFormatter(logging.Formatter("%(name)s: %(message)s"))
    handler.setLevel(level)

    for name in ("uvicorn.error", "app"):
        logging.getLogger(name).addHandler(handler)


async def push_log(level: str, message: str) -> None:
    """Directly push a log entry to Redis from async context."""
    try:
        from app.core.redis import get_redis
        redis = await get_redis()
        entry = json.dumps({
            "t": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "l": level,
            "s": "backend",
            "m": message,
        }, ensure_ascii=False)
        await redis.rpush(_LOG_KEY, entry)
        await redis.ltrim(_LOG_KEY, -_LOG_MAXLEN, -1)
    except Exception:
        pass
