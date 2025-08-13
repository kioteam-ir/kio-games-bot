from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Dict, TypeVar
import copy

from .types import (
    Player,
    Event,
    Cell,
    BoardMatrix,
    Listener
)

T = TypeVar("T", bound="GameEngine")


class GameEngine(ABC):
    """
    Abstract connect-four style engine.
    - Coordinates: row 0..rows-1 (0 top), col 0..cols-1 (0 left)
    """

    def __init__(self, rows: int = 6, cols: int = 7, connect: int = 4) -> None:
        self.rows: int    = rows
        self.cols: int    = cols
        self.connect: int = connect

        self.board: BoardMatrix      = [[Cell.EMPTY] * cols for _ in range(rows)]
        self.column_heights: List[int] = [0] * cols
        self.current_player: Player  = Player.ONE
        self.winner: Optional[Player] = None
        self.ended: bool             = False
        self.move_count: int         = 0
        self.last_move: Optional[Tuple[int, int, Cell]] = None
        self._listeners: Dict[Event, List[Listener]] = {}

        self._add_default_listeners()

    # ---------------------------
    # Observer Pattern
    # ---------------------------
    def _add_default_listeners(self) -> None:
        """Add basic listeners for debugging/logging purposes."""
        def debug_listener(**kwargs):
            print(f"[DEBUG] Event: {kwargs}")

        # Optional: only for debugging, can be removed in production
        self.add_listener(Event.RESET, lambda **k: print("[EVENT] Board reset"))
        self.add_listener(Event.MOVE,  lambda **k: print(f"[EVENT] Move: {k}"))
        self.add_listener(Event.GAME_OVER, lambda **k: print(f"[EVENT] Game over: {k}"))

    def add_listener(self, event: Event, fn: Listener) -> None:
        self._listeners.setdefault(event, []).append(fn)

    def _notify(self, event: Event, *args, **kwargs) -> None:
        for fn in self._listeners.get(event, []):
            try:
                fn(*args, **kwargs)
            except Exception:
                pass  # Optional: log error

    # ---------------------------
    # Core operations
    # ---------------------------
    def reset(self) -> None:
        self.board          = [[Cell.EMPTY] * self.cols for _ in range(self.rows)]
        self.column_heights = [0] * self.cols
        self.current_player = Player.ONE
        self.winner         = None
        self.ended          = False
        self.move_count     = 0
        self.last_move      = None
        self._notify(Event.RESET)

    def clone(self: T) -> T:
        new_engine = copy.copy(self)
        new_engine.board = [row[:] for row in self.board]
        new_engine.column_heights = self.column_heights[:]
        new_engine._listeners = {}
        return new_engine

    def switch_player(self) -> None:
        """Switch turn to the other player."""
        self.current_player = self.current_player.opponent

    # ---------------------------
    # Queries
    # ---------------------------
    def is_column_playable(self, col: int) -> bool:
        return 0 <= col < self.cols and self.column_heights[col] < self.rows and not self.ended

    def legal_moves(self) -> List[int]:
        return [c for c in range(self.cols) if self.is_column_playable(c)]

    def get_board_snapshot(self) -> BoardMatrix:
        return [row[:] for row in self.board]

    def get_column_fill_counts(self) -> List[int]:
        return self.column_heights[:]

    def is_draw(self) -> bool:
        return self.move_count >= self.rows * self.cols and self.winner is None

    # ---------------------------
    # Piece placement helpers
    # ---------------------------
    def _get_next_row_for_col(self, col: int) -> Optional[int]:
        h = self.column_heights[col]
        if h >= self.rows:
            return None
        return self.rows - 1 - h

    def _place_piece_at(self, row: int, col: int, player: Player) -> None:
        self.board[row][col] = player.as_cell
        self.column_heights[col] += 1
        self.move_count += 1
        self.last_move = (row, col, player.as_cell)

    def _undo_piece_at(self, row: int, col: int) -> None:
        self.board[row][col] = Cell.EMPTY
        self.column_heights[col] -= 1
        self.move_count -= 1
        self.last_move = None

    # ---------------------------
    # Win detection
    # ---------------------------
    def _is_winning_from(self, row: int, col: int, player: Player) -> bool:
        directions = ((1, 0), (0, 1), (1, 1), (1, -1))
        for dr, dc in directions:
            count = 1
            # forward
            r, c = row + dr, col + dc
            while 0 <= r < self.rows and 0 <= c < self.cols and self.board[r][c] == player.as_cell:
                count += 1
                r += dr
                c += dc
            # backward
            r, c = row - dr, col - dc
            while 0 <= r < self.rows and 0 <= c < self.cols and self.board[r][c] == player.as_cell:
                count += 1
                r -= dr
                c -= dc
            if count >= self.connect:
                return True
        return False

    # ---------------------------
    # Public move interface
    # ---------------------------
    @abstractmethod
    def make_move(self, col: int) -> bool:
        raise NotImplementedError

    def _finalize_move_after_placement(self, row: int, col: int, player: Player) -> None:
        if self._is_winning_from(row, col, player):
            self.winner = player
            self.ended = True
            self._notify(Event.MOVE, row=row, col=col, player=player)
            self._notify(Event.GAME_OVER, winner=player)
        elif self.is_draw():
            self.ended = True
            self._notify(Event.MOVE, row=row, col=col, player=player)
            self._notify(Event.GAME_OVER, winner=None)
        else:
            self._notify(Event.MOVE, row=row, col=col, player=player)

    # ---------------------------
    # Pretty print
    # ---------------------------
    def pretty(self, symbols: Tuple[str, str] = ("🟢", "🔵")) -> str:
        rows_repr = []
        for r in range(self.rows):
            row_repr = []
            for c in range(self.cols):
                v = self.board[r][c]
                if v.is_empty:
                    row_repr.append("⭕")
                else:
                    row_repr.append(symbols[0] if v == Cell.ONE else symbols[1])
            rows_repr.append(" ".join(row_repr))
        return "\n".join(rows_repr)

    __repr__ = __str__ = pretty
