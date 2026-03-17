import asyncio
import json
from typing import Set


class Broadcaster:
    def __init__(self) -> None:
        self._queues: Set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._queues.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        self._queues.discard(q)

    async def publish(self, event_type: str) -> None:
        if not self._queues:
            return
        payload = json.dumps({"type": event_type})
        for q in list(self._queues):
            await q.put(payload)


broadcaster = Broadcaster()
