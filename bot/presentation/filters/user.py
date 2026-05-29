from __future__ import annotations

from typing import Any

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, InlineQuery, Message

from bot.application.dto.game import ResolvedUserContext
from bot.application.services.game_flow import UserService


def _user_context(kwargs: dict[str, Any]) -> ResolvedUserContext | None:
    ctx = kwargs.get("user_context")
    return ctx if isinstance(ctx, ResolvedUserContext) else None


class ResolvedUserFilter(BaseFilter):
    async def __call__(
        self,
        event: Message | CallbackQuery | InlineQuery,
        user_service: UserService | None = None,
        **kwargs: Any,
    ) -> bool | dict[str, Any]:
        if "user_context" in kwargs:
            return {}
        if user_service is None:
            return False
        from_user = event.from_user
        if from_user is None:
            return False
        context: ResolvedUserContext = await user_service.resolve_user(
            from_user,
            lang_hint=from_user.language_code,
        )
        return {"user_context": context}


class NotBannedFilter(BaseFilter):
    async def __call__(self, **kwargs: Any) -> bool | dict[str, Any]:
        user_context = _user_context(kwargs)
        if user_context is None:
            return False
        if user_context.user.is_banned:
            return False
        return {}


class BannedUserFilter(BaseFilter):
    async def __call__(self, **kwargs: Any) -> bool | dict[str, Any]:
        user_context = _user_context(kwargs)
        if user_context is None:
            return False
        if not user_context.user.is_banned:
            return False
        return {"banned_context": user_context}


class AdminFilter(BaseFilter):
    async def __call__(
        self,
        event: Message,
        container: object,
        **kwargs: Any,
    ) -> bool | dict[str, Any]:
        from bot.core.container import AppContainer

        if not isinstance(container, AppContainer):
            return False
        if event.from_user is None:
            return False
        if event.from_user.id not in container.bot_config.admin_ids:
            return False
        return {}
