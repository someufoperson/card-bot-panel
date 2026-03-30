import asyncio
import json
import logging
from datetime import datetime, timezone

import redis as redis_sync
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from handlers import card_add

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


class _RedisLogHandler(logging.Handler):
    _KEY = "panel:logs"
    _MAXLEN = 1000

    def __init__(self):
        super().__init__()
        self._r = redis_sync.from_url(settings.redis_url, decode_responses=True)

    def emit(self, record: logging.LogRecord):
        try:
            entry = json.dumps({
                "t": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                "l": record.levelname,
                "s": "bot",
                "m": self.format(record),
            }, ensure_ascii=False)
            pipe = self._r.pipeline()
            pipe.rpush(self._KEY, entry)
            pipe.ltrim(self._KEY, -self._MAXLEN, -1)
            pipe.execute()
        except Exception:
            pass


_redis_handler = _RedisLogHandler()
_redis_handler.setFormatter(logging.Formatter("%(name)s: %(message)s"))
logging.getLogger().addHandler(_redis_handler)

logger = logging.getLogger(__name__)


async def main():
    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(card_add.router)

    logger.info("Бот запущен (polling)")
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    asyncio.run(main())
