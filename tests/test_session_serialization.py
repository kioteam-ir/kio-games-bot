from __future__ import annotations

from bot.application.services.game_catalog import GameCatalogService
from bot.domain.entities.game_session import GameSession
from bot.domain.games.registry import create_engine
from bot.domain.games.serialization import snapshot_engine
from bot.domain.schemas.game import GameTypeId
from bot.domain.schemas.player import TelegramPlayer
from bot.domain.schemas.session_store import StoredGameSession, from_stored_session, to_stored_session


def test_session_roundtrip() -> None:
    catalog = GameCatalogService()
    entry = catalog.get("en", GameTypeId.CONNECT_4)
    session = GameSession(
        game_engine=create_engine(entry),
        inline_message_id="inline-99",
        current_player=TelegramPlayer(id=1, first_name="Alice"),
        players=[TelegramPlayer(id=1, first_name="Alice")],
        game_type=GameTypeId.CONNECT_4,
        lang="en",
    )
    stored = to_stored_session(session, game_id=42)
    restored = from_stored_session(stored, entry)
    assert isinstance(restored, GameSession)
    assert restored.lang == "en"
    assert snapshot_engine(restored.game_engine).move_count == 0


def test_stored_session_json_roundtrip() -> None:
    catalog = GameCatalogService()
    entry = catalog.get("fa", GameTypeId.XO)
    session = GameSession(
        game_engine=create_engine(entry),
        inline_message_id="inline-xo",
        current_player=TelegramPlayer(id=7, first_name="Sara"),
        players=[TelegramPlayer(id=7, first_name="Sara")],
        game_type=GameTypeId.XO,
        lang="fa",
    )
    stored = to_stored_session(session, game_id=99)
    stored = StoredGameSession.model_validate_json(stored.model_dump_json())
    loaded = from_stored_session(stored, entry)
    assert isinstance(loaded, GameSession)
    assert loaded.game_type is GameTypeId.XO
