from __future__ import annotations

from typing import Any

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery

from bot.application.services.session_manager import GameSessionManager
from bot.domain.entities.game_session import GameSession
from bot.infrastructure.callback.payloads import MakeGameCallback


class GameSessionFilter(BaseFilter):
    async def __call__(
        self,
        callback_data: object,
        session_manager: GameSessionManager,
        **kwargs: Any,
    ) -> bool | dict[str, Any]:
        game_id = _extract_game_id(callback_data)
        if game_id is None:
            return False
        session = await session_manager.get(game_id)
        if session is None:
            return False
        return {"game_session": session, "game_id": game_id}


class CreatorMatchFilter(BaseFilter):
    async def __call__(
        self,
        callback: CallbackQuery,
        callback_data: MakeGameCallback,
        **kwargs: Any,
    ) -> bool | dict[str, Any]:
        if callback.from_user is None:
            return False
        if callback.from_user.id != callback_data.creator_id:
            return False
        return {"creator_ok": True}


class TwoPlayerSessionFilter(BaseFilter):
    async def __call__(self, event: CallbackQuery | None = None, **kwargs: Any) -> bool | dict[str, Any]:
        _ = event
        game_session = kwargs.get("game_session")
        if not isinstance(game_session, GameSession):
            return False
        if len(game_session.players) != 2:
            return False
        return {"two_player_session": True}


def _extract_game_id(callback_data: object) -> int | None:
    from bot.infrastructure.callback.payloads import CellMoveCallback, JoinGameCallback

    if isinstance(callback_data, JoinGameCallback):
        return callback_data.game_id
    if isinstance(callback_data, CellMoveCallback):
        return callback_data.game_id
    return None
