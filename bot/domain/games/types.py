from enum import IntEnum, StrEnum, auto
from typing import Protocol


# ===========================
# Types
# ===========================
class Event(StrEnum):
    RESET = auto()
    MOVE = auto()
    GAME_OVER = auto()


class Color(StrEnum):
    GREEN = "🟢"
    RED = "🔴"
    BLUE = "🔵"
    YELLOW = "🟡"
    WHITE = "⬜️"


class Symbol(StrEnum):
    X = "❌"
    O = "⭕️"  # noqa: E741
    EMPTY = "⬜️"


class Player(IntEnum):
    ONE = 1
    TWO = 2

    @property
    def as_cell(self) -> "Cell":
        return Cell(self.value)

    @property
    def as_color(self) -> Color:
        color_mapping = (Color.RED, Color.BLUE)
        return color_mapping[self.value - 1]

    @property
    def as_symbol(self) -> Symbol:
        symbol_mapping = (Symbol.X, Symbol.O)
        return symbol_mapping[self.value - 1]

    @property
    def opponent(self) -> "Player":
        return Player.ONE if self == Player.TWO else Player.TWO


class Cell(IntEnum):
    EMPTY = 0
    ONE = Player.ONE
    TWO = Player.TWO

    @property
    def is_empty(self) -> bool:
        return self == Cell.EMPTY

    @property
    def as_player(self) -> Player | None:
        return None if self.is_empty else Player(self.value)

    @property
    def as_color(self) -> Color:
        if self.is_empty:
            return Color.WHITE
        player = self.as_player
        return player.as_color

    @property
    def as_symbol(self) -> Symbol:
        if self.is_empty:
            return Symbol.EMPTY
        player = self.as_player
        return player.as_symbol


BoardMatrix = list[list[Cell]]


class Listener(Protocol):
    def __call__(self, *args, **kwargs) -> None: ...
