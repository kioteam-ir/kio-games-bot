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

    @staticmethod
    def _purge_expired(entries: dict[str, float], now: float) -> None:
        """Remove expired keys from the provided entries mapping in-place."""
        expired = [entry_key for entry_key, expires_at in entries.items() if expires_at <= now]
        for entry_key in expired:
            entries.pop(entry_key, None)

    async def acquire(self, key: str, *, ttl_seconds: int) -> bool:
        now = monotonic()
        async with self._lock:
            self._purge_expired(self._entries, now)
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
