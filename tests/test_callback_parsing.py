from __future__ import annotations

import pytest
from aiogram.types import CallbackQuery, User

from bot.domain.schemas.game import GameTypeId
from bot.infrastructure.callback.parsing import parse_make_game_callback
from bot.infrastructure.callback.payloads import MakeGameCallback
from bot.presentation.filters.callback_data import MakeGameCallbackFilter


def test_parse_legacy_three_part_make_game_callback() -> None:
    parsed = parse_make_game_callback("mg:1369473488:1")
    assert parsed == MakeGameCallback(creator_id=1369473488, game_type=GameTypeId.XO, mine_count=0)


def test_parse_current_four_part_make_game_callback() -> None:
    parsed = parse_make_game_callback("mg:1369473488:4:0")
    assert parsed == MakeGameCallback(creator_id=1369473488, game_type=GameTypeId.CONNECT_5, mine_count=0)


def test_parse_invalid_make_game_callback() -> None:
    assert parse_make_game_callback("mg:bad:data:extra:fields") is None
    assert parse_make_game_callback("jp:42") is None


@pytest.mark.asyncio
async def test_make_game_callback_filter_accepts_legacy_payload() -> None:
    game_filter = MakeGameCallbackFilter()
    callback = CallbackQuery(
        id="1",
        from_user=User(id=42, is_bot=False, first_name="Alice"),
        chat_instance="abc",
        data="mg:42:1",
        inline_message_id="inline-1",
    )

    result = await game_filter(callback)

    assert isinstance(result, dict)
    assert result["callback_data"] == MakeGameCallback(
        creator_id=42,
        game_type=GameTypeId.XO,
        mine_count=0,
    )
