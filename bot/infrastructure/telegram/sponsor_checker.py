from __future__ import annotations

import asyncio
import logging

from aiogram import Bot
from aiogram.enums import ChatMemberStatus

from bot.config.ratelimit import RateLimitConfigClass
from bot.domain.repositories import SponsorMembershipChecker, SponsorRepository
from bot.infrastructure.cache.redis_cache import CacheBackend
from bot.infrastructure.ratelimit.service import RateLimitService

logger = logging.getLogger(__name__)


class TelegramSponsorMembershipChecker(SponsorMembershipChecker):
    def __init__(
        self,
        bot: Bot,
        sponsor_repo: SponsorRepository,
        *,
        cache: CacheBackend | None = None,
        rate_limit_service: RateLimitService | None = None,
        rate_limit_config: RateLimitConfigClass | None = None,
        membership_ttl_seconds: int = 30,
        membership_fail_ttl_seconds: int = 0,
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

    async def is_member_of_all(self, user_id: int, *, force_refresh: bool = False) -> bool:
        sponsors = await self._get_active_sponsors()
        if self._no_sponsors(sponsors):
            return True

        if not force_refresh:
            cached = await self._get_cached_result(user_id, sponsors)
            if cached is True:
                return True

            if not await self._is_rate_allowed(user_id):
                return await self._fallback_to_cache(user_id, sponsors)

        result = await self._check_all_memberships(sponsors, user_id)

        await self._store_result(user_id, sponsors, result)
        return result

    async def invalidate_user(self, user_id: int) -> None:
        if self._cache:
            await self._cache.delete_prefix(f"{self._cache_prefix}{user_id}")

    async def invalidate_all(self) -> None:
        if self._cache:
            await self._cache.delete_prefix(self._cache_prefix)

    # =========================================================
    # Core logic helpers
    # =========================================================

    async def _check_all_memberships(self, sponsors: list, user_id: int) -> bool:
        checks = await asyncio.gather(*(self._is_member(sponsor, user_id) for sponsor in sponsors))
        return all(checks)

    async def _is_member(self, sponsor: object, user_id: int) -> bool:
        sponsor_id = getattr(sponsor, "id", None)
        if sponsor_id is None:
            return False
        try:
            member = await self._bot.get_chat_member(sponsor_id, user_id)
            return self._is_active_member(member.status)
        except Exception as exc:
            err_msg = str(exc).lower()
            sponsor_link = getattr(sponsor, "link", None)
            if "chat not found" in err_msg and sponsor_link:
                resolved_id = await self._try_resolve_and_update_sponsor(sponsor)
                if resolved_id is not None:
                    try:
                        member = await self._bot.get_chat_member(resolved_id, user_id)
                        return self._is_active_member(member.status)
                    except Exception as inner_exc:
                        logger.warning(
                            "Membership check failed after resolving id %s: %s",
                            resolved_id,
                            inner_exc,
                        )
            logger.warning(
                "Membership check failed for user %s in sponsor channel %s: %s",
                user_id,
                sponsor_id,
                exc,
            )
            return False

    async def _try_resolve_and_update_sponsor(self, sponsor: object) -> int | None:
        sponsor_id = getattr(sponsor, "id", None)
        sponsor_link = getattr(sponsor, "link", "")
        username = self._extract_username(sponsor_link)
        if not username:
            return None
        try:
            chat = await self._bot.get_chat(f"@{username}")
            if chat.id and chat.id != sponsor_id:
                logger.info(
                    "Auto-resolving sponsor %s ID from %s to %s",
                    username,
                    sponsor_id,
                    chat.id,
                )
                from api.infrastructure.database.connection import session_scope
                from api.infrastructure.database.models import AppSponser
                from sqlalchemy import update

                async with session_scope() as session:
                    await session.execute(
                        update(AppSponser).where(AppSponser.id == sponsor_id).values(id=chat.id)
                    )
                if hasattr(self._sponsor_repo, "invalidate"):
                    await self._sponsor_repo.invalidate()
                await self.invalidate_all()
                return chat.id
            return chat.id
        except Exception as exc:
            logger.warning("Failed to resolve chat username @%s: %s", username, exc)
            return None

    @staticmethod
    def _extract_username(link: str) -> str | None:
        raw = link.strip()
        if not raw:
            return None
        for prefix in ("https://t.me/", "http://t.me/", "t.me/", "telegram.me/", "@"):
            if raw.startswith(prefix):
                raw = raw[len(prefix):]
                break
        username = raw.split("/")[0].split("?")[0].strip()
        if username and not username.startswith("+"):
            return username
        return None

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

    def _cache_key(self, user_id: int, sponsors: list) -> str:
        s_ids = sorted(getattr(s, "id", 0) for s in sponsors)
        sig = "_".join(str(i) for i in s_ids)
        return f"{self._cache_prefix}{user_id}:{sig}"

    async def _get_cached_result(self, user_id: int, sponsors: list) -> bool | None:
        if not self._cache:
            return None

        cached = await self._cache.get(self._cache_key(user_id, sponsors))
        if cached == "1":
            return True

        return None

    async def _store_result(self, user_id: int, sponsors: list, result: bool) -> None:
        if not self._cache:
            return

        key = self._cache_key(user_id, sponsors)
        if result:
            await self._cache.set(
                key,
                "1",
                ttl_seconds=self._membership_ttl_seconds,
            )
        else:
            await self._cache.delete(key)

    async def _fallback_to_cache(self, user_id: int, sponsors: list) -> bool:
        """
        When rate-limit blocks execution, we rely on last known cached state.
        """
        if not self._cache:
            return False

        cached = await self._cache.get(self._cache_key(user_id, sponsors))
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
