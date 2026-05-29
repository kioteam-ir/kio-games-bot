from __future__ import annotations

from bot.domain.games.base import GameEngine
from bot.domain.schemas.game import GameTypeId
from bot.domain.schemas.player import TelegramPlayer


class GameSession:
    """Runtime game session state (mutable, not a pydantic model)."""

    __slots__ = (
        "game_engine",
        "inline_message_id",
        "current_player",
        "players",
        "game_type",
        "lang",
    )

    def __init__(
        self,
        game_engine: GameEngine,
        inline_message_id: str,
        current_player: TelegramPlayer,
        players: list[TelegramPlayer],
        game_type: GameTypeId,
        lang: str,
    ) -> None:
        self.game_engine = game_engine
        self.inline_message_id = inline_message_id
        self.current_player = current_player
        self.players = players
        self.game_type = game_type
        self.lang = lang

    @property
    def engine(self) -> GameEngine:
        return self.game_engine
