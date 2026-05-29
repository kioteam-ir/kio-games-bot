from __future__ import annotations

from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot.application.services.inline_results import InlineQueryResultService
from bot.core.container import AppContainer
from bot.infrastructure.telegram.keyboards import KeyboardService


class ServicesMiddleware(BaseMiddleware):
    def __init__(self, container: AppContainer) -> None:
        self._keyboards = KeyboardService(container.translator, container.bot_config.bot_username)
        self._inline_results = InlineQueryResultService(container.translator, self._keyboards)
        self._session_config = container.session_config

    async def __call__(
        self,
        handler: Any,
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["keyboards"] = self._keyboards
        data["inline_results"] = self._inline_results
        data["session_config"] = self._session_config
        data["translator"] = self._keyboards._translator
        return await handler(event, data)
