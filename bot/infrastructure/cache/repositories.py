from __future__ import annotations

import json

from bot.domain.repositories import SponsorRepository, UserRepository
from bot.domain.schemas.game import GameTypeId, PlayerGameStats
from bot.domain.schemas.sponsor import SponsorRecord
from bot.domain.schemas.user import UserRecord
from bot.infrastructure.cache.redis_cache import CacheBackend


class CachedUserRepository(UserRepository):
    def __init__(
        self,
        inner: UserRepository,
        cache: CacheBackend,
        *,
        ttl_seconds: int = 120,
        key_prefix: str = "kio:user:",
    ) -> None:
        self._inner = inner
        self._cache = cache
        self._ttl_seconds = ttl_seconds
        self._key_prefix = key_prefix

    def _key(self, user_id: int) -> str:
        return f"{self._key_prefix}{user_id}"

    async def get_or_create(
        self,
        user_id: int,
        *,
        name: str = "",
        username: str = "",
        lang_code: str = "fa",
    ) -> UserRecord:
        cached = await self._cache.get(self._key(user_id))
        if cached is not None:
            return UserRecord.model_validate_json(cached)
        user = await self._inner.get_or_create(
            user_id,
            name=name,
            username=username,
            lang_code=lang_code,
        )
        await self._cache.set(self._key(user_id), user.model_dump_json(), ttl_seconds=self._ttl_seconds)
        return user

    async def change_lang(self, user_id: int, lang_code: str) -> None:
        await self._inner.change_lang(user_id, lang_code)
        await self._cache.delete(self._key(user_id))

    async def get_game_stats(self, user_id: int, game_type: GameTypeId) -> PlayerGameStats:
        return await self._inner.get_game_stats(user_id, game_type)

    async def invalidate(self, user_id: int) -> None:
        await self._cache.delete(self._key(user_id))


class CachedSponsorRepository(SponsorRepository):
    def __init__(
        self,
        inner: SponsorRepository,
        cache: CacheBackend,
        *,
        ttl_seconds: int = 300,
        cache_key: str = "kio:sponsors:active",
    ) -> None:
        self._inner = inner
        self._cache = cache
        self._ttl_seconds = ttl_seconds
        self._cache_key = cache_key

    async def list_active(self) -> list[SponsorRecord]:
        cached = await self._cache.get(self._cache_key)
        if cached is not None:
            payload = json.loads(cached)
            return [SponsorRecord.model_validate(item) for item in payload]
        sponsors = await self._inner.list_active()
        await self._cache.set(
            self._cache_key,
            json.dumps([s.model_dump() for s in sponsors]),
            ttl_seconds=self._ttl_seconds,
        )
        return sponsors

    async def invalidate(self) -> None:
        await self._cache.delete(self._cache_key)
