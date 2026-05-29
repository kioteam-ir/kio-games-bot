from __future__ import annotations

from enum import IntEnum, StrEnum
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from bot.domain.games.ports import GameFamily


class GameTypeId(IntEnum):
    XO = 1
    CONNECT_3 = 2
    CONNECT_4 = 3
    CONNECT_5 = 4
    MINE = 5


class GameResultKind(StrEnum):
    DRAW = "draw"
    PLAYER_1 = "player_1"
    PLAYER_2 = "player_2"


class PlayerGameStats(BaseModel):
    model_config = ConfigDict(frozen=True)

    total: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0


class HeadToHeadStats(BaseModel):
    model_config = ConfigDict(frozen=True)

    total: int
    p1_wins: int
    p2_wins: int
    draws: int


class GameMatchSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    head_to_head: HeadToHeadStats
    result: str


class GameCatalogEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str
    game_type_id: GameTypeId = Field(alias="id")
    description: str
    thumb_url: str
    rows: int
    cols: int
    connect: int

    @property
    def family(self) -> GameFamily:
        from bot.domain.games.registry import family_for

        return family_for(self.game_type_id)

    @property
    def is_xo(self) -> bool:
        """Deprecated: use family == GameFamily.GRID_MARK."""
        from bot.domain.games.ports import GameFamily as GF

        return self.family is GF.GRID_MARK
