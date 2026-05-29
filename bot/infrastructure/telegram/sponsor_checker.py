from __future__ import annotations

from aiogram import Bot

from bot.domain.repositories import SponsorMembershipChecker, SponsorRepository


class TelegramSponsorMembershipChecker(SponsorMembershipChecker):
    def __init__(self, bot: Bot, sponsor_repo: SponsorRepository) -> None:
        self._bot = bot
        self._sponsor_repo = sponsor_repo

    async def is_member_of_all(self, user_id: int) -> bool:
        sponsors = await self._sponsor_repo.list_active()
        for sponsor in sponsors:
            try:
                await self._bot.get_chat_member(sponsor.id, user_id)
            except Exception:
                return False
        return True
