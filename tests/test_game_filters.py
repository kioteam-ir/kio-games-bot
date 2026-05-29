from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import CallbackQuery, User

from bot.infrastructure.callback.payloads import JoinGameCallback
from bot.presentation.filters.game import GameSessionFilter


def _callback() -> CallbackQuery:
    return CallbackQuery(
        id="1",
        from_user=User(id=42, is_bot=False, first_name="Alice"),
        chat_instance="abc",
        inline_message_id="inline-1",
    )


@pytest.mark.asyncio
async def test_game_session_filter_accepts_join_callback_data() -> None:
    session_manager = AsyncMock()
    session_manager.get.return_value = MagicMock()
    game_filter = GameSessionFilter()

    result = await game_filter(
        _callback(),
        session_manager=session_manager,
        callback_data=JoinGameCallback(game_id=7),
    )

    assert result == {"game_session": session_manager.get.return_value, "game_id": 7}
    session_manager.get.assert_awaited_once_with(7)


@pytest.mark.asyncio
async def test_game_session_filter_returns_game_id_when_session_missing() -> None:
    session_manager = AsyncMock()
    session_manager.get.return_value = None
    game_filter = GameSessionFilter()

    result = await game_filter(
        _callback(),
        session_manager=session_manager,
        callback_data=JoinGameCallback(game_id=9),
    )

    assert result == {"game_id": 9, "game_session": None}
