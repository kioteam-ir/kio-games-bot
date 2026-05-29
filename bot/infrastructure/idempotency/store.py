from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from time import monotonic

from redis.asyncio import Redis


class IdempotencyStore(ABC):
    @abstractmethod
    async def acquire(self, key: str, *, ttl_seconds: int) -> bool:
        """Return True when this is the first time the key is seen within TTL."""


class InMemoryIdempotencyStore(IdempotencyStore):
    def __init__(self) -> None:
        self._entries: dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def acquire(self, key: str, *, ttl_seconds: int) -> bool:
        now = monotonic()
        async with self._lock:
            expired = [entry_key for entry_key, expires_at in self._entries.items() if expires_at <= now]
            for entry_key in expired:
                self._entries.pop(entry_key, None)
            if key in self._entries:
                return False
            self._entries[key] = now + ttl_seconds
            return True


class RedisIdempotencyStore(IdempotencyStore):
    def __init__(self, redis: Redis, *, key_prefix: str = "kio:idempotency:") -> None:
        self._redis = redis
        self._key_prefix = key_prefix

    async def acquire(self, key: str, *, ttl_seconds: int) -> bool:
        redis_key = f"{self._key_prefix}{key}"
        acquired = await self._redis.set(redis_key, b"1", nx=True, ex=ttl_seconds)
        return bool(acquired)


def build_idempotency_store(redis: Redis | None) -> IdempotencyStore:
    if redis is None:
        return InMemoryIdempotencyStore()
    return RedisIdempotencyStore(redis)
