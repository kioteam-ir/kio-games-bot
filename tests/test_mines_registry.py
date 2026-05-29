from __future__ import annotations

from bot.application.services.game_catalog import GameCatalogService
from bot.domain.games.mines.with_friend import TurnBasedMinesEngine
from bot.domain.games.ports import GameFamily
from bot.domain.games.registry import create_engine, family_for, get_game_module
from bot.domain.schemas.game import GameTypeId


def test_mine_game_is_registered() -> None:
    entry = GameCatalogService().get("en", GameTypeId.MINE)
    module = get_game_module(entry.game_type_id)
    assert module.game_type_id is GameTypeId.MINE
    assert family_for(GameTypeId.MINE) is GameFamily.MINES


def test_create_mines_engine_with_count() -> None:
    entry = GameCatalogService().get("en", GameTypeId.MINE)
    engine = create_engine(entry, mine_count=15)
    assert isinstance(engine, TurnBasedMinesEngine)
    assert engine.rows == 8
    assert engine.cols == 7
    assert engine.mines == 15


def test_mines_ui_move_via_module() -> None:
    entry = GameCatalogService().get("en", GameTypeId.MINE)
    module = get_game_module(GameTypeId.MINE)
    engine = create_engine(entry, mine_count=5)
    assert module.apply_ui_move(engine, row=1, col=1) is True
    assert engine.revealed_count > 0
