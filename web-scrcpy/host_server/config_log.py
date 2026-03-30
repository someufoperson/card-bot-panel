import json
import os
import sys
from datetime import datetime, timezone

import redis as redis_sync
from loguru import logger

os.makedirs("logs", exist_ok=True)

_REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
_LOG_KEY = "panel:logs"
_LOG_MAXLEN = 1000

try:
    _r = redis_sync.from_url(_REDIS_URL, decode_responses=True)
    _r.ping()
    _redis_available = True
except Exception:
    _redis_available = False


def _redis_sink(message):
    if not _redis_available:
        return
    record = message.record
    try:
        entry = json.dumps({
            "t": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "l": record["level"].name,
            "s": "flask",
            "m": record["message"],
        }, ensure_ascii=False)
        pipe = _r.pipeline()
        pipe.rpush(_LOG_KEY, entry)
        pipe.ltrim(_LOG_KEY, -_LOG_MAXLEN, -1)
        pipe.execute()
    except Exception:
        pass


logger.remove()

logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="DEBUG",
    colorize=True,
)

logger.add(
    _redis_sink,
    format="{message}",
    level="DEBUG",
)

logger.add(
    "logs/sessions.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="INFO",
    rotation="10 MB",
    compression="zip",
    filter=lambda record: record["extra"].get("connection") == True
)