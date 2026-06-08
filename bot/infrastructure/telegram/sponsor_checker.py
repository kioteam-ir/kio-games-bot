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

    # =========================================================
    # Public API
    # =========================================================

    async def is_member_of_all(self, user_id: int) -> bool:
        cached = await self._get_cached_result(user_id)
        if cached is not None:
            return cached

        if not await self._is_rate_allowed(user_id):
            return await self._fallback_to_cache(user_id)

        sponsors = await self._get_active_sponsors()
        if self._no_sponsors(sponsors):
            return True

        result = await self._check_all_memberships(sponsors, user_id)

        await self._store_result(user_id, result)
        return result

    async def invalidate_user(self, user_id: int) -> None:
        if self._cache:
            await self._cache.delete(self._cache_key(user_id))

    async def invalidate_all(self) -> None:
        if self._cache:
            await self._cache.delete_prefix(self._cache_prefix)

    # =========================================================
    # Core logic helpers
    # =========================================================

    async def _check_all_memberships(self, sponsors: list, user_id: int) -> bool:
        checks = await asyncio.gather(*(self._is_member(sponsor.id, user_id) for sponsor in sponsors))
        return all(checks)

    async def _is_member(self, sponsor_id: int, user_id: int) -> bool:
        try:
            member = await self._bot.get_chat_member(sponsor_id, user_id)
            return self._is_active_member(member.status)
        except Exception:
            return False

    @staticmethod
    def _is_active_member(status: ChatMemberStatus) -> bool:
        return status not in {ChatMemberStatus.LEFT, ChatMemberStatus.KICKED}

    # =========================================================
    # Sponsor data helpers
    # =========================================================

    async def _get_active_sponsors(self):
        return await self._sponsor_repo.list_active()

    @staticmethod
    def _no_sponsors(sponsors: list) -> bool:
        return not sponsors

    # =========================================================
    # Cache layer
    # =========================================================

    def _cache_key(self, user_id: int) -> str:
        return f"{self._cache_prefix}{user_id}"

    async def _get_cached_result(self, user_id: int) -> bool | None:
        if not self._cache:
            return None

        cached = await self._cache.get(self._cache_key(user_id))
        if cached is None:
            return None

        return cached == "1"

    async def _store_result(self, user_id: int, result: bool) -> None:
        if not self._cache:
            return

        ttl = self._membership_ttl_seconds if result else self._membership_fail_ttl_seconds

        await self._cache.set(
            self._cache_key(user_id),
            "1" if result else "0",
            ttl_seconds=ttl,
        )

    async def _fallback_to_cache(self, user_id: int) -> bool:
        """
        When rate-limit blocks execution, we rely on last known cached state.
        """
        if not self._cache:
            return False

        cached = await self._cache.get(self._cache_key(user_id))
        return cached == "1"

    # =========================================================
    # Rate limiting
    # =========================================================

    async def _is_rate_allowed(self, user_id: int) -> bool:
        if not self._rate_limit_service:
            return True

        return await self._rate_limit_service.allow(
            "sponsor_check",
            user_id,
            self._rate_limit_config.sponsor_check,
        )
