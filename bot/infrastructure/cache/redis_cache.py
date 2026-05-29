from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from time import monotonic

from redis.asyncio import Redis


class CacheBackend(ABC):
    @abstractmethod
    async def get(self, key: str) -> str | None: ...

    @abstractmethod
    async def set(self, key: str, value: str, *, ttl_seconds: int) -> None: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...

    @abstractmethod
    async def delete_prefix(self, prefix: str) -> None: ...


class InMemoryCacheBackend(CacheBackend):
    def __init__(self) -> None:
        self._entries: dict[str, tuple[str, float]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> str | None:
        now = monotonic()
        async with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            value, expires_at = entry
            if expires_at <= now:
                self._entries.pop(key, None)
                return None
            return value

    async def set(self, key: str, value: str, *, ttl_seconds: int) -> None:
        async with self._lock:
            self._entries[key] = (value, monotonic() + ttl_seconds)

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._entries.pop(key, None)

    async def delete_prefix(self, prefix: str) -> None:
        async with self._lock:
            for key in [k for k in self._entries if k.startswith(prefix)]:
                self._entries.pop(key, None)


class RedisCacheBackend(CacheBackend):
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def get(self, key: str) -> str | None:
        raw = await self._redis.get(key)
        if raw is None:
            return None
        if isinstance(raw, bytes):
            return raw.decode()
        return str(raw)

    async def set(self, key: str, value: str, *, ttl_seconds: int) -> None:
        await self._redis.set(key, value, ex=ttl_seconds)

    async def delete(self, key: str) -> None:
        await self._redis.delete(key)

    async def delete_prefix(self, prefix: str) -> None:
        cursor = 0
        while True:
            cursor, keys = await self._redis.scan(cursor=cursor, match=f"{prefix}*", count=200)
            if keys:
                await self._redis.delete(*keys)
            if cursor == 0:
                break


def build_cache_backend(redis: Redis | None) -> CacheBackend:
    if redis is None:
        return InMemoryCacheBackend()
    return RedisCacheBackend(redis)
