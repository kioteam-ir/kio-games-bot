from __future__ import annotations

from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram.utils.i18n import SimpleI18nMiddleware

from bot.application.services.game_flow import UserService
from bot.config.i18n import I18nConfigClass


class UserLocaleMiddleware(BaseMiddleware):
    """Resolve persisted user locale before i18n middleware runs."""

    def __init__(self, user_service: UserService, i18n_config: I18nConfigClass) -> None:
        self._user_service = user_service
        self._i18n_config = i18n_config

    async def __call__(
        self,
        handler: Any,
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        from_user = getattr(event, "from_user", None)
        if from_user is not None:
            context = await self._user_service.resolve_user(
                from_user,
                lang_hint=from_user.language_code,
            )
            data["user_context"] = context
            data["locale"] = context.lang
        else:
            data["locale"] = self._i18n_config.default_lang
        return await handler(event, data)


class KioI18nMiddleware(SimpleI18nMiddleware):
    async def get_locale(self, event: TelegramObject, data: dict[str, Any]) -> str:
        locale = data.get("locale")
        if isinstance(locale, str):
            return locale
        from_user = getattr(event, "from_user", None)
        if from_user and from_user.language_code in self.i18n.available_locales:
            return str(from_user.language_code)
        return str(self.i18n.default_locale)
