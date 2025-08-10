from typing import List, Optional, Protocol, TypeVar
from enum import StrEnum, IntEnum, auto

# ===========================
# Types
# ===========================
class Event(StrEnum):
    RESET     = auto()
    MOVE      = auto()
    GAME_OVER = auto()


class Player(IntEnum):
    ONE = 1
    TWO = 2

    @property
    def as_cell(self) -> 'Cell':
        return Cell(self.value)

    @property
    def opponent(self) -> 'Player':
        return Player.ONE if self == Player.TWO else Player.TWO


class Cell(IntEnum):
    EMPTY = 0
    ONE   = Player.ONE
    TWO   = Player.TWO

    @property
    def is_empty(self) -> bool:
        return self == Cell.EMPTY

    @property
    def as_player(self) -> Optional[Player]:
        return None if self.is_empty else Player(self.value)


BoardMatrix = List[List[Cell]]


class Listener(Protocol):
    def __call__(self, *args, **kwargs) -> None: ...