from __future__ import annotations

from bot.domain.games.mines.with_friend import TurnBasedMinesEngine
from bot.domain.games.types import Player


def test_first_safe_reveal_switches_turn() -> None:
    engine = TurnBasedMinesEngine(rows=3, cols=3, mines=1, seed=42)
    assert engine.make_move((0, 0)) is True
    assert engine.current_player is Player.TWO
    assert engine.scores[Player.ONE] > 0


def test_revealed_cell_rejected() -> None:
    engine = TurnBasedMinesEngine(rows=3, cols=3, mines=1, seed=7)
    assert engine.apply_ui_move(row=1, col=1) is True
    assert engine.apply_ui_move(row=1, col=1) is False


def test_is_draw_when_scores_tie_at_end() -> None:
    engine = TurnBasedMinesEngine(rows=2, cols=2, mines=0, seed=1)
    engine.place_mines(0, 0)
    engine.started = True
    for r in range(engine.rows):
        for c in range(engine.cols):
            cell = engine.board[r][c]
            cell.revealed = True
            cell.owner = Player.ONE if (r + c) % 2 == 0 else Player.TWO
            engine.revealed_count += 1
            engine.scores[cell.owner] += 1
    engine.ended = True
    engine.winner = engine._determine_winner()
    assert engine.is_draw() is True
