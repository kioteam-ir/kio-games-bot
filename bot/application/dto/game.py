from pydantic import BaseModel, ConfigDict

from bot.domain.entities.game_session import GameSession
from bot.domain.schemas.game import GameCatalogEntry, GameMatchSummary, GameTypeId
from bot.domain.schemas.player import TelegramPlayer
from bot.domain.schemas.user import UserRecord
from bot.locales.i18n_keys import I18nKeys


class UseCaseError(BaseModel):
    model_config = ConfigDict(frozen=True)

    message_key: I18nKeys
    alert: bool = True


class GameBoardView(BaseModel):
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    text: str
    game_id: int
    game_over: bool
    session: GameSession


class CreateGameResult(BaseModel):
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    text: str
    game_id: int
    session: GameSession


class JoinGameResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    view: GameBoardView


class MoveGameResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    view: GameBoardView
    match_summary: GameMatchSummary | None = None
    should_delete_session: bool = False


class PlayerStatsResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str


class ChangeLangResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    alert_text: str


class SessionTimeoutResult(BaseModel):
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    inline_message_id: str
    text: str
    game_id: int
    game_over: bool
    session: GameSession


class InlineGamesContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    user: UserRecord
    lang: str
    games: list[GameCatalogEntry]
    is_banned: bool = False


class ResolvedUserContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    user: UserRecord
    lang: str


class MakeGameRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    creator: TelegramPlayer
    game_type: GameTypeId
    inline_message_id: str
    lang: str


class JoinGameRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    player: TelegramPlayer
    game_id: int
    lang: str


class MoveGameRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    player_id: int
    game_id: int
    row: int
    col: int
    lang: str
