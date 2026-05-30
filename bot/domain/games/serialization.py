from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from bot.domain.games.base import GameEngine
from bot.domain.games.mines.with_friend import MineCell, TurnBasedMinesEngine
from bot.domain.games.registry import create_engine
from bot.domain.games.types import Cell, Player
from bot.domain.schemas.game import GameCatalogEntry


class BoardEngineSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    variant: Literal["board"] = "board"
    board: list[list[int]]
    column_heights: list[int]
    current_player: int
    winner: int | None
    ended: bool
    move_count: int
    rows: int
    cols: int
    connect: int


class MinesCellSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    has_mine: bool
    revealed: bool
    adjacent: int
    owner: int | None


class MinesEngineSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    variant: Literal["mines"] = "mines"
    rows: int
    cols: int
    mines: int
    started: bool
    revealed_count: int
    current_player: int
    winner: int | None
    ended: bool
    scores: tuple[int, int]
    mine_hits: tuple[int, int]
    board: list[list[MinesCellSnapshot]]


EngineSnapshot = BoardEngineSnapshot | MinesEngineSnapshot


def snapshot_engine(engine: GameEngine | TurnBasedMinesEngine) -> EngineSnapshot:
    if isinstance(engine, TurnBasedMinesEngine):
        return MinesEngineSnapshot(
            rows=engine.rows,
            cols=engine.cols,
            mines=engine.mines,
            started=engine.started,
            revealed_count=engine.revealed_count,
            current_player=int(engine.current_player),
            winner=int(engine.winner) if engine.winner is not None else None,
            ended=engine.ended,
            scores=(engine.scores[Player.ONE], engine.scores[Player.TWO]),
            mine_hits=(engine.mine_hits[Player.ONE], engine.mine_hits[Player.TWO]),
            board=[
                [
                    MinesCellSnapshot(
                        has_mine=cell.has_mine,
                        revealed=cell.revealed,
                        adjacent=cell.adjacent,
                        owner=int(cell.owner) if cell.owner is not None else None,
                    )
                    for cell in row
                ]
                for row in engine.board
            ],
        )
    return BoardEngineSnapshot(
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


def restore_engine(snapshot: EngineSnapshot, entry: GameCatalogEntry) -> GameEngine | TurnBasedMinesEngine:
    if snapshot.variant == "mines":
        if not isinstance(snapshot, MinesEngineSnapshot):
            msg = "Expected MinesEngineSnapshot"
            raise TypeError(msg)
        engine = TurnBasedMinesEngine(snapshot.rows, snapshot.cols, snapshot.mines)
        engine.started = snapshot.started
        engine.revealed_count = snapshot.revealed_count
        engine.current_player = Player(snapshot.current_player)
        engine.winner = Player(snapshot.winner) if snapshot.winner is not None else None
        engine.ended = snapshot.ended
        engine.scores = {Player.ONE: snapshot.scores[0], Player.TWO: snapshot.scores[1]}
        mine_hits = getattr(snapshot, "mine_hits", (0, 0))
        engine.mine_hits = {Player.ONE: mine_hits[0], Player.TWO: mine_hits[1]}
        engine.board = [
            [
                MineCell(
                    has_mine=cell.has_mine,
                    revealed=cell.revealed,
                    adjacent=cell.adjacent,
                    owner=Player(cell.owner) if cell.owner is not None else None,
                )
                for cell in row
            ]
            for row in snapshot.board
        ]
        if snapshot.rows != entry.rows or snapshot.cols != entry.cols:
            msg = "Mines engine snapshot dimensions do not match catalog entry"
            raise ValueError(msg)
        return engine

    if not isinstance(snapshot, BoardEngineSnapshot):
        msg = "Expected BoardEngineSnapshot"
        raise TypeError(msg)
    engine = create_engine(entry)
    if not isinstance(engine, GameEngine):
        msg = "Board snapshot requires a board-style engine"
        raise TypeError(msg)
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
