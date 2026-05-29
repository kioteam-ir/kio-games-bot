from __future__ import annotations

from typing import Any

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from bot.application.dto.game import ResolvedUserContext
from bot.core.container import AppContainer
from bot.domain.schemas.texts import CommandKey


class SponsorOkFilter(BaseFilter):
    async def __call__(
        self,
        event: Message | CallbackQuery,
        container: AppContainer,
        **kwargs: Any,
    ) -> bool | dict[str, Any]:
        if container.sponsor_checker is None:
            return False
        user = event.from_user
        if user is None:
            return False
        if not await container.sponsor_checker.is_member_of_all(user.id):
            return False
        return {"sponsors_ok": True}


class SponsorRequiredFilter(BaseFilter):
    async def __call__(
        self,
        event: Message | CallbackQuery,
        container: AppContainer,
        user_context: ResolvedUserContext,
        **kwargs: Any,
    ) -> bool | dict[str, Any]:
        if container.sponsor_checker is None:
            return False
        user = event.from_user
        if user is None:
            return False
        if await container.sponsor_checker.is_member_of_all(user.id):
            return False
        sponsors = await container.sponsor_repo.list_active()
        return {
            "sponsor_required": True,
            "sponsors": sponsors,
            "join_message": container.texts.get(user_context.lang, CommandKey.JOIN_FIRST),
        }
