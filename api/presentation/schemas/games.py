from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from bot.application.dto.board import BoardState
from bot.domain.schemas.game import GameMatchSummary, GameTypeId
from bot.domain.schemas.player import TelegramPlayer


class CreateGameBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    creator: TelegramPlayer
    game_type: GameTypeId
    inline_message_id: str
    lang: str = "en"


class JoinGameBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    player: TelegramPlayer
    lang: str = "en"


class MoveGameBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    player_id: int
    row: int = Field(ge=0)
    col: int = Field(ge=1)
    lang: str = "en"


class GameBoardResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str
    game_id: int
    game_over: bool
    board: BoardState


class CreateGameResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    game_id: int
    text: str


class MoveGameResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    view: GameBoardResponse
    match_summary: GameMatchSummary | None = None
    should_delete_session: bool = False


class ApiErrorResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    message_key: str
    alert: bool = True


LangCode = Literal["tr", "en", "fa"]
