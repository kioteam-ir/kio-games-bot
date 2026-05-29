from __future__ import annotations

from dataclasses import dataclass

from bot.domain.games.base import GameEngine
from bot.domain.games.connect.with_friend import VsFriendEngine
from bot.domain.games.mines.with_friend import MineCell, TurnBasedMinesEngine
from bot.domain.games.ports import GameFamily, GameModule
from bot.domain.games.types import Cell
from bot.domain.games.XO.with_friend import VsFriendXO
from bot.domain.schemas.game import GameCatalogEntry, GameTypeId


@dataclass(frozen=True, slots=True)
class BoardGameModule:
    game_type_id: GameTypeId
    family: GameFamily

    def create_engine(self, entry: GameCatalogEntry, *, mine_count: int | None = None) -> GameEngine:
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
        if not isinstance(cell, Cell):
            msg = f"Expected Cell, got {type(cell)!r}"
            raise TypeError(msg)
        if self.family is GameFamily.GRID_MARK:
            return str(cell.as_symbol)
        return str(cell.as_color)

    def uses_column_picker(self) -> bool:
        return self.family is GameFamily.CONNECT_DROP


@dataclass(frozen=True, slots=True)
class MinesGameModule:
    game_type_id: GameTypeId = GameTypeId.MINE
    family: GameFamily = GameFamily.MINES

    def create_engine(self, entry: GameCatalogEntry, *, mine_count: int | None = None) -> TurnBasedMinesEngine:
        mines = mine_count if mine_count is not None else entry.connect
        return TurnBasedMinesEngine(entry.rows, entry.cols, mines)

    def apply_ui_move(self, engine: GameEngine, *, row: int, col: int) -> bool:
        if not isinstance(engine, TurnBasedMinesEngine):
            return False
        return engine.apply_ui_move(row=row, col=col)

    def cell_display(self, engine: GameEngine, cell: object) -> str:
        if not isinstance(cell, MineCell):
            msg = f"Expected MineCell, got {type(cell)!r}"
            raise TypeError(msg)
        return cell.display_label()

    def uses_column_picker(self) -> bool:
        return False


GAME_MODULES: dict[GameTypeId, GameModule] = {
    GameTypeId.XO: BoardGameModule(GameTypeId.XO, GameFamily.GRID_MARK),
    GameTypeId.CONNECT_3: BoardGameModule(GameTypeId.CONNECT_3, GameFamily.CONNECT_DROP),
    GameTypeId.CONNECT_4: BoardGameModule(GameTypeId.CONNECT_4, GameFamily.CONNECT_DROP),
    GameTypeId.CONNECT_5: BoardGameModule(GameTypeId.CONNECT_5, GameFamily.CONNECT_DROP),
    GameTypeId.MINE: MinesGameModule(),
}


def get_game_module(game_type: GameTypeId) -> GameModule:
    module = GAME_MODULES.get(game_type)
    if module is None:
        msg = f"No game module registered for {game_type!r}"
        raise KeyError(msg)
    return module


def family_for(game_type: GameTypeId) -> GameFamily:
    return get_game_module(game_type).family


def create_engine(entry: GameCatalogEntry, *, mine_count: int | None = None) -> GameEngine | TurnBasedMinesEngine:
    return get_game_module(entry.game_type_id).create_engine(entry, mine_count=mine_count)


def register_game_module(module: GameModule) -> None:
    """Register or replace a game module at runtime (tests / future plugins)."""
    GAME_MODULES[module.game_type_id] = module
