from __future__ import annotations

from bot.domain.games.connect.with_friend import VsFriendEngine
from bot.domain.games.mines.with_friend import TurnBasedMinesEngine, mines_to_win
from bot.domain.games.move_outcome import MoveRejectReason
from bot.domain.games.types import Player


def test_mines_to_win_is_dynamic() -> None:
    assert mines_to_win(9) == 5
    assert mines_to_win(5) == 3
    assert mines_to_win(15) == 8


def test_mine_win_when_more_than_half_found() -> None:
    engine = TurnBasedMinesEngine(rows=4, cols=4, mines=5, seed=99)
    engine.started = True
    engine.board[0][0].has_mine = True
    engine.board[0][1].has_mine = True
    engine.board[0][2].has_mine = True
    engine.board[1][0].has_mine = True
    engine.board[1][1].has_mine = True
    for r in range(engine.rows):
        for c in range(engine.cols):
            if not engine.board[r][c].has_mine:
                engine.board[r][c].adjacent = 1

    assert engine.make_move((0, 0)) is True
    assert engine.mine_hits[Player.ONE] == 1
    assert not engine.ended

    assert engine.make_move((0, 1)) is True
    assert engine.mine_hits[Player.ONE] == 2
    assert not engine.ended

    assert engine.make_move((0, 2)) is True
    assert engine.mine_hits[Player.ONE] == 3
    assert engine.ended is True
    assert engine.winner is Player.ONE


def test_revealed_cell_classified() -> None:
    engine = TurnBasedMinesEngine(rows=3, cols=3, mines=1, seed=7)
    assert engine.apply_ui_move(row=1, col=1) is True
    assert engine.classify_ui_move(row=1, col=1) is MoveRejectReason.CELL_ALREADY_REVEALED


def test_connect_grid_click_uses_column() -> None:
    engine = VsFriendEngine(rows=6, cols=7, connect=4)
    assert engine.classify_ui_move(row=3, col=4) is None
    assert engine.apply_ui_move(row=3, col=4) is True
    assert engine.move_count == 1


def test_connect_full_column_classified() -> None:
    engine = VsFriendEngine(rows=2, cols=3, connect=3)
    for _ in range(2):
        engine.make_move(1)
        engine.make_move(1)
    assert engine.classify_ui_move(row=0, col=2) is MoveRejectReason.COLUMN_FULL
