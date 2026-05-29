from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from bot.domain.games.serialization import EngineSnapshot, restore_engine, snapshot_engine
from bot.domain.schemas.game import GameCatalogEntry, GameTypeId
from bot.domain.schemas.player import TelegramPlayer


class StoredGameSession(BaseModel):
    model_config = ConfigDict(frozen=True)

    game_id: int
    game_type: GameTypeId
    lang: str
    inline_message_id: str
    players: tuple[TelegramPlayer, ...]
    current_player_id: int
    engine: EngineSnapshot


def to_stored_session(session: object, *, game_id: int) -> StoredGameSession:
    from bot.domain.entities.game_session import GameSession

    if not isinstance(session, GameSession):
        msg = f"Expected GameSession, got {type(session)!r}"
        raise TypeError(msg)
    return StoredGameSession(
        game_id=game_id,
        game_type=session.game_type,
        lang=session.lang,
        inline_message_id=session.inline_message_id,
        players=tuple(session.players),
        current_player_id=session.current_player.id,
        engine=snapshot_engine(session.game_engine),
    )


def from_stored_session(stored: StoredGameSession, entry: GameCatalogEntry) -> object:
    from bot.domain.entities.game_session import GameSession

    current_player = next(player for player in stored.players if player.id == stored.current_player_id)
    return GameSession(
        game_engine=restore_engine(stored.engine, entry),
        inline_message_id=stored.inline_message_id,
        current_player=current_player,
        players=list(stored.players),
        game_type=stored.game_type,
        lang=stored.lang,
    )
