from __future__ import annotations

import copy
import random
from dataclasses import dataclass
from typing import TypeVar

from bot.domain.games.move_outcome import MoveRejectReason
from bot.domain.games.types import Event, Listener, Player

T = TypeVar("T", bound="TurnBasedMinesEngine")

_NUMBER_LABELS = {
    1: "1️⃣",
    2: "2️⃣",
    3: "3️⃣",
    4: "4️⃣",
    5: "5️⃣",
    6: "6️⃣",
    7: "7️⃣",
    8: "8️⃣",
}


def mines_to_win(mine_count: int) -> int:
    """Mines a player must find to win (strictly more than half)."""
    return mine_count // 2 + 1


@dataclass(slots=True)
class MineCell:
    has_mine: bool = False
    revealed: bool = False
    adjacent: int = 0
    owner: Player | None = None

    def display_label(self) -> str:
        if not self.revealed:
            return "⬜"
        if self.has_mine:
            if self.owner == Player.ONE:
                return "🔴"
            if self.owner == Player.TWO:
                return "🔵"
            return "💣"
        return _NUMBER_LABELS.get(self.adjacent, str(self.adjacent)) if self.adjacent > 0 else "ㅤ"


class TurnBasedMinesEngine:
    """
    Turn-based minesweeper for two players.

    - First click places mines (safe zone around the click).
    - Hitting a mine keeps the current player's turn.
    - Revealing safe cells switches turn to the opponent.
    - Winner is the first player to find more than half of the mines.
    """

    def __init__(
        self,
        rows: int = 8,
        cols: int = 7,
        mines: int = 9,
        seed: int | None = None,
    ) -> None:
        self.rows = rows
        self.cols = cols
        self.mines = mines
        self._seed = seed

        self.board: list[list[MineCell]] = [[MineCell() for _ in range(cols)] for _ in range(rows)]
        self.started = False
        self.ended = False
        self.revealed_count = 0

        self.current_player = Player.ONE
        self.winner: Player | None = None
        self.scores: dict[Player, int] = {Player.ONE: 0, Player.TWO: 0}
        self.mine_hits: dict[Player, int] = {Player.ONE: 0, Player.TWO: 0}

        self._listeners: dict[Event, list[Listener]] = {}
        self._add_default_listeners()

    @property
    def mines_to_win(self) -> int:
        return mines_to_win(self.mines)

    def _add_default_listeners(self) -> None:
        self.add_listener(Event.RESET, lambda **k: None)
        self.add_listener(Event.MOVE, lambda **k: None)
        self.add_listener(Event.GAME_OVER, lambda **k: None)

    def add_listener(self, event: Event, fn: Listener) -> None:
        self._listeners.setdefault(event, []).append(fn)

    def _notify(self, event: Event, *args, **kwargs) -> None:
        for fn in self._listeners.get(event, []):
            try:
                fn(*args, **kwargs)
            except Exception:
                pass

    def reset(self) -> None:
        self.board = [[MineCell() for _ in range(self.cols)] for _ in range(self.rows)]
        self.started = False
        self.ended = False
        self.revealed_count = 0
        self.current_player = Player.ONE
        self.winner = None
        self.scores = {Player.ONE: 0, Player.TWO: 0}
        self.mine_hits = {Player.ONE: 0, Player.TWO: 0}
        self._notify(Event.RESET)

    def clone(self: T) -> T:
        new_eng = copy.copy(self)
        new_eng.board = [[MineCell() for _ in range(self.cols)] for _ in range(self.rows)]
        for r in range(self.rows):
            for c in range(self.cols):
                src = self.board[r][c]
                dst = new_eng.board[r][c]
                dst.has_mine = src.has_mine
                dst.revealed = src.revealed
                dst.adjacent = src.adjacent
                dst.owner = src.owner
        new_eng._listeners = {}
        return new_eng

    def in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.rows and 0 <= col < self.cols

    def neighbors(self, row: int, col: int):
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                r, c = row + dr, col + dc
                if self.in_bounds(r, c):
                    yield r, c

    def place_mines(self, safe_row: int, safe_col: int) -> None:
        rng = random.Random(self._seed)
        coords = [(r, c) for r in range(self.rows) for c in range(self.cols)]
        safe_zone = {(safe_row, safe_col)} | set(self.neighbors(safe_row, safe_col))
        coords = [point for point in coords if point not in safe_zone]
        rng.shuffle(coords)
        for r, c in coords[: self.mines]:
            self.board[r][c].has_mine = True
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c].has_mine:
                    continue
                self.board[r][c].adjacent = sum(
                    1 for nr, nc in self.neighbors(r, c) if self.board[nr][nc].has_mine
                )

    def is_draw(self) -> bool:
        return self.ended and self.winner is None

    def classify_ui_move(self, *, row: int, col: int) -> MoveRejectReason | None:
        if row <= 0 or col <= 0:
            return MoveRejectReason.INVALID
        board_row, board_col = row - 1, col - 1
        if not self.in_bounds(board_row, board_col):
            return MoveRejectReason.INVALID
        if self.board[board_row][board_col].revealed:
            return MoveRejectReason.CELL_ALREADY_REVEALED
        return None

    def make_move(self, move: tuple[int, int]) -> bool:
        if self.ended:
            return False
        row, col = move
        if not self.in_bounds(row, col):
            return False
        cell = self.board[row][col]
        if cell.revealed:
            return False

        if not self.started:
            self.place_mines(row, col)
            self.started = True

        if cell.has_mine:
            cell.revealed = True
            cell.owner = self.current_player
            self.revealed_count += 1
            self.scores[self.current_player] += 1
            self.mine_hits[self.current_player] += 1
            self._notify(
                Event.MOVE,
                row=row,
                col=col,
                player=self.current_player,
                revealed_count=1,
                exploded=True,
            )
            if self._check_mine_win(self.current_player):
                return True
            return True

        changed = 0
        stack = [(row, col)]
        while stack:
            r, c = stack.pop()
            cur = self.board[r][c]
            if cur.revealed:
                continue
            cur.revealed = True
            cur.owner = self.current_player
            changed += 1
            self.revealed_count += 1
            if cur.adjacent == 0:
                for nr, nc in self.neighbors(r, c):
                    neigh = self.board[nr][nc]
                    if not neigh.revealed and not neigh.has_mine:
                        stack.append((nr, nc))

        if changed > 0:
            self.scores[self.current_player] += changed
            self._notify(
                Event.MOVE,
                row=row,
                col=col,
                player=self.current_player,
                revealed_count=changed,
                exploded=False,
            )

        self.current_player = self.current_player.opponent

        if self.revealed_count == self.rows * self.cols:
            self.ended = True
            self.winner = self._determine_winner()
            self._notify(Event.GAME_OVER, winner=self.winner)

        return changed > 0

    def apply_ui_move(self, *, row: int, col: int) -> bool:
        if self.classify_ui_move(row=row, col=col) is not None:
            return False
        return self.make_move((row - 1, col - 1))

    def _check_mine_win(self, player: Player) -> bool:
        if self.mine_hits[player] > self.mines // 2:
            self.ended = True
            self.winner = player
            self._notify(Event.GAME_OVER, winner=self.winner)
            return True
        return False

    def _determine_winner(self) -> Player | None:
        p1 = self.scores.get(Player.ONE, 0)
        p2 = self.scores.get(Player.TWO, 0)
        if p1 > p2:
            return Player.ONE
        if p2 > p1:
            return Player.TWO
        return None
