from __future__ import annotations

from bot.application.services.board_state import BoardStateBuilder
from bot.application.services.game_catalog import GameCatalogService
from bot.domain.entities.game_session import GameSession
from bot.domain.games.registry import create_engine
from bot.domain.schemas.game import GameTypeId
from bot.domain.schemas.player import TelegramPlayer


def test_board_state_for_connect_has_column_picker() -> None:
    entry = GameCatalogService().get("en", GameTypeId.CONNECT_4)
    session = GameSession(
        game_engine=create_engine(entry),
        inline_message_id="inline-1",
        current_player=TelegramPlayer(id=1, first_name="Alice"),
        players=[
            TelegramPlayer(id=1, first_name="Alice"),
            TelegramPlayer(id=2, first_name="Bob"),
        ],
        game_type=GameTypeId.CONNECT_4,
        lang="en",
    )
    board = BoardStateBuilder.build(session, game_id=10, game_over=False)
    assert board.column_picker is not None
    assert len(board.rows) == entry.rows
    assert len(board.players) == 2


def test_board_state_for_xo_has_no_column_picker() -> None:
    entry = GameCatalogService().get("en", GameTypeId.XO)
    session = GameSession(
        game_engine=create_engine(entry),
        inline_message_id="inline-2",
        current_player=TelegramPlayer(id=1, first_name="Alice"),
        players=[
            TelegramPlayer(id=1, first_name="Alice"),
            TelegramPlayer(id=2, first_name="Bob"),
        ],
        game_type=GameTypeId.XO,
        lang="en",
    )
    board = BoardStateBuilder.build(session, game_id=11, game_over=False)
    assert board.column_picker is None
    assert len(board.rows) == entry.rows
