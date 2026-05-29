from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from bot.domain.games.base import GameEngine
from bot.domain.games.registry import create_engine
from bot.domain.games.types import Cell, Player
from bot.domain.schemas.game import GameCatalogEntry


class EngineSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    board: list[list[int]]
    column_heights: list[int]
    current_player: int
    winner: int | None
    ended: bool
    move_count: int
    rows: int
    cols: int
    connect: int


def snapshot_engine(engine: GameEngine) -> EngineSnapshot:
    return EngineSnapshot(
        board=[[int(cell) for cell in row] for row in engine.board],
        column_heights=engine.column_heights[:],
        current_player=int(engine.current_player),
        winner=int(engine.winner) if engine.winner is not None else None,
        ended=engine.ended,
        move_count=engine.move_count,
        rows=engine.rows,
        cols=engine.cols,
        connect=engine.connect,
    )


def restore_engine(snapshot: EngineSnapshot, entry: GameCatalogEntry) -> GameEngine:
    engine = create_engine(entry)
    engine.board = [[Cell(value) for value in row] for row in snapshot.board]
    engine.column_heights = snapshot.column_heights[:]
    engine.current_player = Player(snapshot.current_player)
    engine.winner = Player(snapshot.winner) if snapshot.winner is not None else None
    engine.ended = snapshot.ended
    engine.move_count = snapshot.move_count
    if snapshot.rows != engine.rows or snapshot.cols != engine.cols or snapshot.connect != engine.connect:
        msg = "Engine snapshot dimensions do not match catalog entry"
        raise ValueError(msg)
    return engine
