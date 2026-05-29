from __future__ import annotations

import pytest

from bot.config.ratelimit import RateLimitAlgorithm, RateLimitConfigClass, RateLimitRule
from bot.infrastructure.cache.redis_cache import InMemoryCacheBackend
from bot.infrastructure.cache.repositories import CachedSponsorRepository, CachedUserRepository
from bot.infrastructure.ratelimit.service import InMemoryRateLimitBackend, RateLimitService


class FakeSponsorRepo:
    def __init__(self) -> None:
        self.calls = 0

    async def list_active(self) -> list[object]:
        self.calls += 1
        return []


class FakeUserRepo:
    def __init__(self) -> None:
        self.calls = 0

    async def get_or_create(self, user_id: int, **kwargs: object) -> object:
        from datetime import UTC, datetime

        from bot.domain.schemas.user import UserRecord

        self.calls += 1
        return UserRecord(
            id=user_id,
            is_banned=False,
            is_superuser=False,
            lang_code="en",
            joined_time=datetime.now(tz=UTC),
            username="alice",
            name="Alice",
        )

    async def change_lang(self, user_id: int, lang_code: str) -> None:
        return None

    async def get_game_stats(self, user_id: int, game_type: object) -> object:
        from bot.domain.schemas.game import PlayerGameStats

        return PlayerGameStats()


@pytest.mark.asyncio
async def test_cached_sponsor_repository_hits_db_once() -> None:
    cache = InMemoryCacheBackend()
    inner = FakeSponsorRepo()
    repo = CachedSponsorRepository(inner, cache, ttl_seconds=60)

    await repo.list_active()
    await repo.list_active()

    assert inner.calls == 1


@pytest.mark.asyncio
async def test_cached_user_repository_hits_db_once() -> None:
    cache = InMemoryCacheBackend()
    inner = FakeUserRepo()
    repo = CachedUserRepository(inner, cache, ttl_seconds=60)

    await repo.get_or_create(1)
    await repo.get_or_create(1)

    assert inner.calls == 1


@pytest.mark.asyncio
async def test_fixed_window_rate_limit_blocks_extra_requests() -> None:
    service = RateLimitService(
        InMemoryRateLimitBackend(),
        RateLimitConfigClass(enabled=True),
    )
    rule = RateLimitRule(
        algorithm=RateLimitAlgorithm.FIXED_WINDOW,
        max_requests=2,
        window_seconds=60,
    )
    assert await service.allow("test", 1, rule) is True
    assert await service.allow("test", 1, rule) is True
    assert await service.allow("test", 1, rule) is False


@pytest.mark.asyncio
async def test_token_bucket_rate_limit_allows_burst() -> None:
    service = RateLimitService(
        InMemoryRateLimitBackend(),
        RateLimitConfigClass(enabled=True),
    )
    rule = RateLimitRule(
        algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
        max_requests=3,
        window_seconds=1,
        capacity=3,
        refill_per_second=0.0,
    )
    assert await service.allow("move", 9, rule) is True
    assert await service.allow("move", 9, rule) is True
    assert await service.allow("move", 9, rule) is True
    assert await service.allow("move", 9, rule) is False


@pytest.mark.asyncio
async def test_sliding_window_rate_limit_blocks_after_threshold() -> None:
    service = RateLimitService(
        InMemoryRateLimitBackend(),
        RateLimitConfigClass(enabled=True),
    )
    rule = RateLimitRule(
        algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
        max_requests=2,
        window_seconds=60,
    )
    assert await service.allow("callback", 7, rule) is True
    assert await service.allow("callback", 7, rule) is True
    assert await service.allow("callback", 7, rule) is False
