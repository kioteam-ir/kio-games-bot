from __future__ import annotations

from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot.core.container import AppContainer


class ContainerMiddleware(BaseMiddleware):
    def __init__(self, container: AppContainer) -> None:
        self._container = container

    async def __call__(
        self,
        handler: Any,
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["container"] = self._container
        data["translator"] = self._container.translator
        data["user_service"] = self._container.user_service
        data["inline_games_service"] = self._container.inline_games_service
        data["change_language_service"] = self._container.change_language_service
        data["player_stats_service"] = self._container.player_stats_service
        data["game_flow_service"] = self._container.game_flow_service
        data["session_manager"] = self._container.session_manager
        data["sponsor_repo"] = self._container.sponsor_repo
        return await handler(event, data)
