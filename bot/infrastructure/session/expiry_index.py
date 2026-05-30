from __future__ import annotations

import time

from redis.asyncio import Redis


class SessionExpiryIndex:
    """Persistent expiry schedule in Redis (survives bot restarts)."""

    def __init__(self, redis: Redis, *, key: str = "kio:sessions:expiry") -> None:
        self._redis = redis
        self._key = key

    async def schedule(self, game_id: int, *, expires_at: float) -> None:
        await self._redis.zadd(self._key, {str(game_id): expires_at})

    async def remove(self, game_id: int) -> None:
        await self._redis.zrem(self._key, str(game_id))

    async def pop_due(self, *, limit: int) -> list[int]:
        now = time.time()
        raw_ids = await self._redis.zrangebyscore(self._key, "-inf", now, start=0, num=limit)
        due: list[int] = []
        for raw in raw_ids:
            game_id = int(raw.decode() if isinstance(raw, bytes) else raw)
            removed = await self._redis.zrem(self._key, str(game_id))
            if removed:
                due.append(game_id)
        return due
