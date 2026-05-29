from __future__ import annotations

import asyncio

from aiogram import Bot
from aiogram.enums import ChatMemberStatus

from bot.config.ratelimit import RateLimitConfigClass
from bot.domain.repositories import SponsorMembershipChecker, SponsorRepository
from bot.infrastructure.cache.redis_cache import CacheBackend
from bot.infrastructure.ratelimit.service import RateLimitService


class TelegramSponsorMembershipChecker(SponsorMembershipChecker):
    def __init__(
        self,
        bot: Bot,
        sponsor_repo: SponsorRepository,
        *,
        cache: CacheBackend | None = None,
        rate_limit_service: RateLimitService | None = None,
        rate_limit_config: RateLimitConfigClass | None = None,
        membership_ttl_seconds: int = 300,
        membership_fail_ttl_seconds: int = 60,
        cache_prefix: str = "kio:sponsor:member:",
    ) -> None:
        self._bot = bot
        self._sponsor_repo = sponsor_repo
        self._cache = cache
        self._rate_limit_service = rate_limit_service
        self._rate_limit_config = rate_limit_config or RateLimitConfigClass()
        self._membership_ttl_seconds = membership_ttl_seconds
        self._membership_fail_ttl_seconds = membership_fail_ttl_seconds
        self._cache_prefix = cache_prefix

    def _cache_key(self, user_id: int) -> str:
        return f"{self._cache_prefix}{user_id}"

    async def is_member_of_all(self, user_id: int) -> bool:
        if self._cache is not None:
            cached = await self._cache.get(self._cache_key(user_id))
            if cached is not None:
                return cached == "1"

        if self._rate_limit_service is not None and not await self._rate_limit_service.allow(
            "sponsor_check",
            user_id,
            self._rate_limit_config.sponsor_check,
        ):
            if self._cache is not None:
                cached = await self._cache.get(self._cache_key(user_id))
                if cached is not None:
                    return cached == "1"
            return False

        sponsors = await self._sponsor_repo.list_active()
        if not sponsors:
            return True

        checks = await asyncio.gather(
            *[self._is_member(sponsor.id, user_id) for sponsor in sponsors],
        )
        result = all(checks)
        if self._cache is not None:
            ttl = self._membership_ttl_seconds if result else self._membership_fail_ttl_seconds
            await self._cache.set(self._cache_key(user_id), "1" if result else "0", ttl_seconds=ttl)
        return result

    async def invalidate_user(self, user_id: int) -> None:
        if self._cache is not None:
            await self._cache.delete(self._cache_key(user_id))

    async def invalidate_all(self) -> None:
        if self._cache is not None:
            await self._cache.delete_prefix(self._cache_prefix)

    async def _is_member(self, sponsor_id: int, user_id: int) -> bool:
        try:
            member = await self._bot.get_chat_member(sponsor_id, user_id)
        except Exception:
            return False
        return member.status not in {ChatMemberStatus.LEFT, ChatMemberStatus.KICKED}
