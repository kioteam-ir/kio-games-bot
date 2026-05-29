from __future__ import annotations

from bot.application.services.game_catalog import GameCatalogService
from bot.domain.games.connect.with_friend import VsFriendEngine
from bot.domain.games.ports import GameFamily
from bot.domain.games.registry import create_engine, family_for, get_game_module
from bot.domain.games.XO.with_friend import VsFriendXO
from bot.domain.schemas.game import GameCatalogEntry, GameTypeId


def _entry(game_type: GameTypeId) -> GameCatalogEntry:
    return GameCatalogService().get("en", game_type)


def test_all_catalog_games_are_registered() -> None:
    catalog = GameCatalogService()
    for game_type in GameTypeId:
        entry = catalog.get("en", game_type)
        module = get_game_module(entry.game_type_id)
        assert module.game_type_id is game_type


def test_family_mapping() -> None:
    assert family_for(GameTypeId.XO) is GameFamily.GRID_MARK
    assert family_for(GameTypeId.CONNECT_4) is GameFamily.CONNECT_DROP


def test_create_connect_engine() -> None:
    engine = create_engine(_entry(GameTypeId.CONNECT_4))
    assert isinstance(engine, VsFriendEngine)
    assert engine.rows == 6
    assert engine.cols == 7


def test_create_xo_engine() -> None:
    engine = create_engine(_entry(GameTypeId.XO))
    assert isinstance(engine, VsFriendXO)


def test_connect_ui_move_via_module() -> None:
    module = get_game_module(GameTypeId.CONNECT_4)
    engine = create_engine(_entry(GameTypeId.CONNECT_4))
    assert module.apply_ui_move(engine, row=0, col=1) is True
    assert engine.move_count == 1


def test_xo_ui_move_via_module() -> None:
    module = get_game_module(GameTypeId.XO)
    engine = create_engine(_entry(GameTypeId.XO))
    assert module.apply_ui_move(engine, row=1, col=1) is True
    assert engine.move_count == 1
