from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple, Dict, Any

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class Cell(Enum):
    EMPTY = "ㅤ" #empty char
    RED = "🔴"
    YELLOW = "🔵"

    def __str__(self) -> str:
        return self.value


@dataclass
class ConnectNGame:

    rows: int = 7   # Changed to 7 rows
    cols: int = 8   # Changed to 8 columns
    win_len: int = 4
    board: Optional[List[List[Cell]]] = None
    turn: Cell = Cell.RED
    winner: Optional[Cell] = None
    last_move: Optional[Tuple[int, int]] = None  # (row, col)


    def __init__(self,win_len:int=4,rows:int=7,cols:int=8) : 
        self.cols = cols
        self.rows = rows 
        self.win_len = win_len


    def __post_init__(self) -> None:
        if self.board is None:
            self.board = [[Cell.EMPTY for _ in range(self.cols)] for _ in range(self.rows)]
        if len(self.board) != self.rows or any(len(r) != self.cols for r in self.board):
            raise ValueError("board shape does not match rows/cols")

    def render(self) -> str:
        return "\n".join("".join(str(cell) for cell in row) for row in self.board)

    def get_valid_moves(self) -> List[int]:
        return [c for c in range(self.cols) if self.board[0][c] == Cell.EMPTY]

    def is_full(self) -> bool:
        return all(cell != Cell.EMPTY for cell in self.board[0])

    def make_move(self, col: int) -> Tuple[int, int]:
        if self.winner is not None:
            raise RuntimeError("game already finished")
        if not (0 <= col < self.cols):
            raise ValueError("column out of range")

        for r in range(self.rows - 1, -1, -1):
            if self.board[r][col] == Cell.EMPTY:
                self.board[r][col] = self.turn
                self.last_move = (r, col)

                if self._is_winner_from(r, col):
                    self.winner = self.turn
                else:
                    self._switch_turn()
                return (r, col)

        raise ValueError("column is full")

    def _switch_turn(self) -> None:
        self.turn = Cell.YELLOW if self.turn == Cell.RED else Cell.RED

    def _is_winner_from(self, r: int, c: int) -> bool:
        piece = self.board[r][c]
        if piece == Cell.EMPTY:
            return False
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            count = 1 + self._count_direction(r, c, dr, dc) + self._count_direction(r, c, -dr, -dc)
            if count >= self.win_len:
                return True
        return False

    def _count_direction(self, r: int, c: int, dr: int, dc: int) -> int:
        piece = self.board[r][c]
        cnt = 0
        rr, cc = r + dr, c + dc
        while 0 <= rr < self.rows and 0 <= cc < self.cols and self.board[rr][cc] == piece:
            cnt += 1
            rr += dr
            cc += dc
        return cnt

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rows": self.rows,
            "cols": self.cols,
            "win_len": self.win_len,
            "board": [[cell.value for cell in row] for row in self.board],
            "turn": self.turn.value,
            "winner": self.winner.value if self.winner else None,
            "last_move": list(self.last_move) if self.last_move else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Connect4Game":
        rows = int(data["rows"])
        cols = int(data["cols"])
        win_len = int(data.get("win_len", 4))
        raw_board = data["board"]
        board = [[Cell(cell) for cell in row] for row in raw_board]
        turn = Cell(data["turn"])
        winner = Cell(data["winner"]) if data.get("winner") else None
        last_move = tuple(data["last_move"]) if data.get("last_move") else None
        return cls(rows=rows, cols=cols, win_len=win_len, board=board, turn=turn, winner=winner, last_move=last_move)

    def make_inline_keyboard_board(self, prefix: str = "drop") -> InlineKeyboardMarkup:
        buttons: List[List[InlineKeyboardButton]] = []

        clickable_positions = {}
        for col in range(self.cols):
            for row in range(self.rows):
                if self.board[row][col] == Cell.EMPTY:
                    clickable_positions[(row, col)] = True
                    break

        for row in range(self.rows):
            row_buttons = []
            for col in range(self.cols):
                cell = self.board[row][col]
                if (row, col) in clickable_positions:
                    row_buttons.append(
                        InlineKeyboardButton(
                            str(cell),
                            callback_data=f"{prefix}_{col}"
                        )
                    )
                else:
                    row_buttons.append(
                        InlineKeyboardButton(
                            str(cell),
                            callback_data="noop"
                        )
                    )
            buttons.append(row_buttons)

        return InlineKeyboardMarkup(buttons)



z = ConnectNGame()
print(z.board)