from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from time import monotonic, time

from redis.asyncio import Redis

from bot.config.ratelimit import RateLimitAlgorithm, RateLimitConfigClass, RateLimitRule


class RateLimitBackend(ABC):
    @abstractmethod
    async def allow(self, key: str, rule: RateLimitRule) -> bool: ...


class InMemoryRateLimitBackend(RateLimitBackend):
    def __init__(self) -> None:
        self._fixed: dict[str, tuple[int, float]] = {}
        self._sliding: dict[str, list[float]] = {}
        self._buckets: dict[str, tuple[float, float]] = {}
        self._lock = asyncio.Lock()

    async def allow(self, key: str, rule: RateLimitRule) -> bool:
        async with self._lock:
            if rule.algorithm == RateLimitAlgorithm.FIXED_WINDOW:
                return self._fixed_window(key, rule)
            if rule.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
                return self._sliding_window(key, rule)
            return self._token_bucket(key, rule)

    def _fixed_window(self, key: str, rule: RateLimitRule) -> bool:
        now = monotonic()
        count, expires_at = self._fixed.get(key, (0, 0.0))
        if expires_at <= now:
            count = 0
            expires_at = now + rule.window_seconds
        if count >= rule.max_requests:
            self._fixed[key] = (count, expires_at)
            return False
        self._fixed[key] = (count + 1, expires_at)
        return True

    def _sliding_window(self, key: str, rule: RateLimitRule) -> bool:
        now = monotonic()
        events = [ts for ts in self._sliding.get(key, []) if ts > now - rule.window_seconds]
        if len(events) >= rule.max_requests:
            self._sliding[key] = events
            return False
        events.append(now)
        self._sliding[key] = events
        return True

    def _token_bucket(self, key: str, rule: RateLimitRule) -> bool:
        capacity = rule.capacity or rule.max_requests
        refill = rule.refill_per_second or (capacity / max(rule.window_seconds, 1))
        now = monotonic()
        tokens, last = self._buckets.get(key, (float(capacity), now))
        tokens = min(float(capacity), tokens + (now - last) * refill)
        if tokens < 1.0:
            self._buckets[key] = (tokens, now)
            return False
        self._buckets[key] = (tokens - 1.0, now)
        return True


class RedisRateLimitBackend(RateLimitBackend):
    def __init__(self, redis: Redis, *, key_prefix: str) -> None:
        self._redis = redis
        self._key_prefix = key_prefix

    def _key(self, key: str) -> str:
        return f"{self._key_prefix}{key}"

    async def allow(self, key: str, rule: RateLimitRule) -> bool:
        if rule.algorithm == RateLimitAlgorithm.FIXED_WINDOW:
            return await self._fixed_window(key, rule)
        if rule.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            return await self._sliding_window(key, rule)
        return await self._token_bucket(key, rule)

    async def _fixed_window(self, key: str, rule: RateLimitRule) -> bool:
        redis_key = self._key(f"fixed:{key}")
        count = await self._redis.incr(redis_key)
        if count == 1:
            await self._redis.expire(redis_key, rule.window_seconds)
        return count <= rule.max_requests

    async def _sliding_window(self, key: str, rule: RateLimitRule) -> bool:
        redis_key = self._key(f"slide:{key}")
        now = time()
        member = f"{now:.6f}"
        pipe = self._redis.pipeline()
        pipe.zremrangebyscore(redis_key, 0, now - rule.window_seconds)
        pipe.zadd(redis_key, {member: now})
        pipe.zcard(redis_key)
        pipe.expire(redis_key, rule.window_seconds)
        _, _, count, _ = await pipe.execute()
        return int(count) <= rule.max_requests

    async def _token_bucket(self, key: str, rule: RateLimitRule) -> bool:
        redis_key = self._key(f"bucket:{key}")
        capacity = float(rule.capacity or rule.max_requests)
        refill = rule.refill_per_second or (capacity / max(rule.window_seconds, 1))
        now = monotonic()
        raw = await self._redis.hgetall(redis_key)
        if not raw:
            await self._redis.hset(redis_key, mapping={"tokens": capacity - 1, "ts": now})
            await self._redis.expire(redis_key, max(rule.window_seconds * 2, 60))
            return True
        tokens = float(raw.get(b"tokens") or raw.get("tokens") or capacity)
        last = float(raw.get(b"ts") or raw.get("ts") or now)
        tokens = min(capacity, tokens + (now - last) * refill)
        if tokens < 1.0:
            await self._redis.hset(redis_key, mapping={"tokens": tokens, "ts": now})
            return False
        await self._redis.hset(redis_key, mapping={"tokens": tokens - 1.0, "ts": now})
        return True


class RateLimitService:
    def __init__(self, backend: RateLimitBackend, config: RateLimitConfigClass) -> None:
        self._backend = backend
        self._config = config

    @property
    def enabled(self) -> bool:
        return self._config.enabled

    async def allow(self, scope: str, subject_id: int, rule: RateLimitRule) -> bool:
        if not self._config.enabled:
            return True
        key = f"{scope}:{subject_id}"
        return await self._backend.allow(key, rule)


def build_rate_limit_service(redis: Redis | None, config: RateLimitConfigClass | None = None) -> RateLimitService:
    cfg = config or RateLimitConfigClass()
    if redis is None:
        backend: RateLimitBackend = InMemoryRateLimitBackend()
    else:
        backend = RedisRateLimitBackend(redis, key_prefix=cfg.key_prefix)
    return RateLimitService(backend, cfg)
