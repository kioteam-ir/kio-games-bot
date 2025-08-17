from typing import List, Optional, Protocol, TypeVar
from enum import StrEnum, IntEnum, auto

# ===========================
# Types
# ===========================
class Event(StrEnum):
    RESET     = auto()
    MOVE      = auto()
    GAME_OVER = auto()

class Color(StrEnum):
    GREEN  = '🟢'
    RED    = '🔴'
    BLUE   = '🔵'
    YELLOW = '🟡'
    white  = '⬜️'

class Player(IntEnum):
    ONE = 1
    TWO = 2

    @property
    def as_cell(self) -> 'Cell':
        return Cell(self.value)
    
    @property
    def as_color(self) -> Color:
        color_mapping = (Color.GREEN, Color.BLUE)
        return color_mapping[self.value - 1]
    @property
    def as_symbol(self) -> str:
        symbol_mapping = ('X', 'O')
        return symbol_mapping[self.value - 1]

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
    
    @property
    def as_color(self) -> Color:
        if self.is_empty:
            return Color.white
        player = self.as_player
        return player.as_color
        

BoardMatrix = List[List[Cell]]


class Listener(Protocol):
    def __call__(self, *args, **kwargs) -> None: ...