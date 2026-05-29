from __future__ import annotations

from typing import TYPE_CHECKING, Union

from bot.domain.games.connect.with_friend import VsFriendEngine
from bot.domain.games.XO.with_friend import VsFriendXO
from bot.domain.schemas.game import GameTypeId
from bot.domain.schemas.player import TelegramPlayer

if TYPE_CHECKING:
    from bot.domain.games.base import GameEngine

GameEngineType = Union[VsFriendXO, VsFriendEngine]


class GameSession:
    """Runtime game session state (mutable, not a pydantic model)."""

    __slots__ = (
        "game_engine",
        "inline_message_id",
        "current_player",
        "players",
        "is_xo",
        "game_type",
    )

    def __init__(
        self,
        game_engine: GameEngineType,
        inline_message_id: str,
        current_player: TelegramPlayer,
        players: list[TelegramPlayer],
        is_xo: bool,
        game_type: GameTypeId,
    ) -> None:
        self.game_engine = game_engine
        self.inline_message_id = inline_message_id
        self.current_player = current_player
        self.players = players
        self.is_xo = is_xo
        self.game_type = game_type

    @property
    def engine(self) -> GameEngine:
        return self.game_engine
