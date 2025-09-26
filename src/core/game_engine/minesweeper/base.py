from __future__ import annotations
from typing import List, Optional, Tuple, Dict, Set, Generator, TypeVar, overload, Any
import copy
import random
from dataclasses import dataclass, field

from ..types import Listener, Player, Event

T = TypeVar("T", bound="TurnBasedMinesEngine")


@dataclass(frozen=True)
class Coord:
    row: int
    col: int


@dataclass(slots=True)
class Cell:
    """Internal cell representation for the turn-based mines engine."""

    has_mine: bool = False
    revealed: bool = False
    adjacent: int  = 0
        # owner: which player revealed this cell (None if still hidden)
    owner: Optional[Player] = None

    def __repr__(self) -> str:
        if not self.revealed:
            return "⬜"
        if self.has_mine:
            return "💣"
        return str(self.adjacent) if self.adjacent > 0 else "ㅤ"


class TurnBasedMinesEngine:
    """
    Turn-based Mines-style engine that matches the architecture/style of your
    `GameEngine` (observer pattern, reset/clone/pretty), but tailored to a
    multiplayer turn-based ruleset:

    - Construct with rows, cols, mines, optional seed.
    - Players alternate turns (Player.ONE starts).
    - `make_move((r, c))` reveals a cell.
      * If the revealed cell contains a mine -> the revealing player keeps the turn ("reward").
      * Otherwise the turn switches to the other player.
    - No flags in this variant.
    - Score is number of cells a player has revealed (mines count too).
    - Game ends when all cells are revealed; winner is player with higher score
      or `None` in case of tie.

    Events used (consistent with your other engines):
    - Event.RESET (no kwargs)
    - Event.MOVE -> kwargs: row, col, player, revealed_count, exploded (bool)
    - Event.GAME_OVER -> kwargs: winner: Optional[Player]
    """

    def __init__(self, rows: int = 9, cols: int = 9, mines: int = 10, seed: Optional[int] = None) -> None:
        self.rows : int = rows
        self.cols : int = cols
        self.mines: int = mines
        self._seed      = seed

        self.board: List[List[Cell]] = [[Cell() for _ in range(cols)] for _ in range(rows)]
        self.started: bool = False
        self.ended: bool = False
        self.revealed_count: int = 0

        # turn management / scoring
        self.current_player: Player    = Player.ONE
        self.winner: Optional[Player]  = None
        self.scores: Dict[Player, int] = {Player.ONE: 0, Player.TWO: 0}

        self._listeners: Dict[Event, List[Listener]] = {}
        self._add_default_listeners()

    # ---------------------------
    # Observer Pattern
    # ---------------------------
    def _add_default_listeners(self) -> None:
        self.add_listener(Event.RESET, lambda **k: print("[EVENT] Mines reset"))
        self.add_listener(Event.MOVE, lambda **k: None)
        self.add_listener(Event.GAME_OVER, lambda **k: print(f"[EVENT] Game over: {k}"))

    def add_listener(self, event: Event, fn: Listener) -> None:
        self._listeners.setdefault(event, []).append(fn)

    def _notify(self, event: Event, *args, **kwargs) -> None:
        for fn in self._listeners.get(event, []):
            try:
                fn(*args, **kwargs)
            except Exception:
                pass

    # ---------------------------
    # Board setup & utilities
    # ---------------------------
    def reset(self) -> None:
        """Reset engine to initial state; mines placed on first reveal."""
        self.board = [[Cell() for _ in range(self.cols)] for _ in range(self.rows)]
        self.started = False
        self.ended = False
        self.revealed_count = 0
        self.current_player = Player.ONE
        self.scores = {Player.ONE: 0, Player.TWO: 0}
        self._notify(Event.RESET)

    def clone(self: T) -> T:
        new_eng = copy.copy(self)
        new_eng.board = [[Cell() for _ in range(self.cols)] for _ in range(self.rows)]
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

    def neighbors(self, row: int, col: int) -> Generator[Tuple[int, int], Any, None]:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                r, c = row + dr, col + dc
                if self.in_bounds(r, c):
                    yield r, c

    def place_mines(self, safe_row: int, safe_col: int) -> None:
        """Place mines randomly while guaranteeing the first-click safe zone is mine-free."""
        rng = random.Random(self._seed)
        coords = [(r, c) for r in range(self.rows) for c in range(self.cols)]
        safe_zone = {(safe_row, safe_col)} | { (r,c) for r,c in self.neighbors(safe_row, safe_col) }
        coords = [p for p in coords if p not in safe_zone]
        rng.shuffle(coords)
        chosen = coords[: self.mines]
        for r, c in chosen:
            self.board[r][c].has_mine = True
        # compute adjacent counts
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c].has_mine:
                    continue
                count = sum(1 for (nr, nc) in self.neighbors(r, c) if self.board[nr][nc].has_mine)
                self.board[r][c].adjacent = count

    # ---------------------------
    # Queries
    # ---------------------------
    @property
    def legal_moves(self) -> Set[Tuple[int, int]]:
        s: Set[Tuple[int, int]] = set()
        for r in range(self.rows):
            for c in range(self.cols):
                if not self.board[r][c].revealed:
                    s.add((r, c))
        return s

    @property
    def is_finished(self) -> bool:
        return self.ended

    # ---------------------------
    # Move logic (turn-based)
    # ---------------------------
    def make_move(self, move: Tuple[int, int]) -> bool:
        """Reveal cell at (row, col).

        Returns True if the move changed the board (a hidden cell was revealed).
        Turn switching behavior:
            - if player reveals a mine -> the same player keeps the turn (reward)
            - otherwise -> turn switches to opponent
        """
        if self.ended:
            return False
        row, col = move
        if not self.in_bounds(row, col):
            return False
        cell = self.board[row][col]
        if cell.revealed:
            return False

        # On first reveal, place mines avoiding the clicked cell
        if not self.started:
            self.place_mines(row, col)
            self.started = True

        # If cell is a mine -> reveal it, award point, player continues
        if cell.has_mine:
            cell.revealed = True
            cell.owner = self.current_player
            self.revealed_count += 1
            self.scores[self.current_player] += 1
            self._notify(Event.MOVE, row=row, col=col, player=self.current_player, revealed_count=1, exploded=True)
            # check end
            if self.revealed_count == self.rows * self.cols:
                self.ended = True
                winner = self._determine_winner()
                self._notify(Event.GAME_OVER, winner=winner)
            # same player continues (reward)
            return True

        # Safe cell: reveal region (BFS-like) and award points equal to newly revealed cells
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
            self._notify(Event.MOVE, row=row, col=col, player=self.current_player, revealed_count=changed, exploded=False)

        # after revealing safe cells, turn switches to opponent
        self.current_player = self.current_player.opponent

        # check end condition
        if self.revealed_count == self.rows * self.cols:
            self.ended = True
            self.winner = self._determine_winner()
            self._notify(Event.GAME_OVER, winner=self.winner)

        return changed > 0

    def _determine_winner(self) -> Optional[Player]:
        p1 = self.scores.get(Player.ONE, 0)
        p2 = self.scores.get(Player.TWO, 0)
        if p1 > p2:
            return Player.ONE
        if p2 > p1:
            return Player.TWO
        return None

    # ---------------------------
    # Pretty print
    # ---------------------------
    def pretty(self, reveal_all: bool = False) -> str:
        rows_repr: List[str] = []
        for r in range(self.rows):
            row_repr: List[str] = []
            for c in range(self.cols):
                cell = self.board[r][c]
                if cell.revealed or reveal_all:
                    if cell.has_mine:
                        row_repr.append("💣")
                    else:
                        row_repr.append(f' {cell.adjacent}' if cell.adjacent > 0 else "ㅤ")
                else:
                    row_repr.append("⬜")
            rows_repr.append(" ".join(row_repr))
        score_line = f"Scores: P1={self.scores.get(Player.ONE,0)} P2={self.scores.get(Player.TWO,0)} Current={self.current_player}"
        return "\n".join(rows_repr) + "\n" + score_line

    __repr__ = __str__ = pretty