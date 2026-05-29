from __future__ import annotations

from dataclasses import dataclass

from bot.domain.games.base import GameEngine
from bot.domain.games.connect.with_friend import VsFriendEngine
from bot.domain.games.ports import GameFamily, GameModule
from bot.domain.games.XO.with_friend import VsFriendXO
from bot.domain.schemas.game import GameCatalogEntry, GameTypeId


@dataclass(frozen=True, slots=True)
class BoardGameModule:
    game_type_id: GameTypeId
    family: GameFamily

    def create_engine(self, entry: GameCatalogEntry) -> GameEngine:
        if self.family is GameFamily.GRID_MARK:
            return VsFriendXO(entry.rows, entry.connect)
        return VsFriendEngine(entry.rows, entry.cols, entry.connect)

    def apply_ui_move(self, engine: GameEngine, *, row: int, col: int) -> bool:
        if self.family is GameFamily.GRID_MARK:
            if not isinstance(engine, VsFriendXO):
                return False
            return engine.apply_ui_move(row=row, col=col)
        if not isinstance(engine, VsFriendEngine):
            return False
        return engine.apply_ui_move(row=row, col=col)

    def cell_display(self, engine: GameEngine, cell: object) -> str:
        from bot.domain.games.types import Cell

        if not isinstance(cell, Cell):
            msg = f"Expected Cell, got {type(cell)!r}"
            raise TypeError(msg)
        if self.family is GameFamily.GRID_MARK:
            return str(cell.as_symbol)
        return str(cell.as_color)

    def uses_column_picker(self) -> bool:
        return self.family is GameFamily.CONNECT_DROP


GAME_MODULES: dict[GameTypeId, BoardGameModule] = {
    GameTypeId.XO: BoardGameModule(GameTypeId.XO, GameFamily.GRID_MARK),
    GameTypeId.CONNECT_3: BoardGameModule(GameTypeId.CONNECT_3, GameFamily.CONNECT_DROP),
    GameTypeId.CONNECT_4: BoardGameModule(GameTypeId.CONNECT_4, GameFamily.CONNECT_DROP),
    GameTypeId.CONNECT_5: BoardGameModule(GameTypeId.CONNECT_5, GameFamily.CONNECT_DROP),
}


def get_game_module(game_type: GameTypeId) -> GameModule:
    module = GAME_MODULES.get(game_type)
    if module is None:
        msg = f"No game module registered for {game_type!r}"
        raise KeyError(msg)
    return module


def family_for(game_type: GameTypeId) -> GameFamily:
    return get_game_module(game_type).family


def create_engine(entry: GameCatalogEntry) -> GameEngine:
    return get_game_module(entry.game_type_id).create_engine(entry)


def register_game_module(module: BoardGameModule) -> None:
    """Register or replace a game module at runtime (tests / future plugins)."""
    GAME_MODULES[module.game_type_id] = module
