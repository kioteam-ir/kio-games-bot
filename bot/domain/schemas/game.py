from enum import IntEnum, StrEnum

from pydantic import BaseModel, ConfigDict, Field


class GameTypeId(IntEnum):
    XO = 1
    CONNECT_3 = 2
    CONNECT_4 = 3
    CONNECT_5 = 4


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
    def is_xo(self) -> bool:
        return self.game_type_id == GameTypeId.XO
