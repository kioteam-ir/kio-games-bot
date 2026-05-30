from __future__ import annotations

import time
from unittest.mock import AsyncMock

import pytest

from bot.application.services.game_catalog import GameCatalogService
from bot.application.services.session_manager import GameSessionManager, InMemoryGameSessionStorage
from bot.domain.entities.game_session import GameSession
from bot.domain.games.registry import create_engine
from bot.domain.schemas.game import GameTypeId
from bot.domain.schemas.player import TelegramPlayer
from bot.infrastructure.session.expiry_index import SessionExpiryIndex


@pytest.mark.asyncio
async def test_expire_notifies_handlers_for_waiting_session() -> None:
    catalog = GameCatalogService()
    entry = catalog.get("fa", GameTypeId.XO)
    session = GameSession(
        game_engine=create_engine(entry),
        inline_message_id="inline-waiting",
        current_player=TelegramPlayer(id=1, first_name="Ali"),
        players=[TelegramPlayer(id=1, first_name="Ali")],
        game_type=GameTypeId.XO,
        lang="fa",
    )
    manager = GameSessionManager(
        InMemoryGameSessionStorage(),
        timeout=60.0,
        cleanup_batch_size=10,
    )
    notified: list[tuple[int, GameSession]] = []

    async def on_deleted(game_id: int, deleted: GameSession) -> None:
        notified.append((game_id, deleted))

    manager.subscribe("session_deleted", on_deleted)
    game_id = await manager.push(session)
    await manager.expire(game_id)

    assert notified == [(game_id, session)]
    assert await manager.get(game_id) is None


@pytest.mark.asyncio
async def test_delete_does_not_notify_handlers() -> None:
    catalog = GameCatalogService()
    entry = catalog.get("fa", GameTypeId.XO)
    session = GameSession(
        game_engine=create_engine(entry),
        inline_message_id="inline-done",
        current_player=TelegramPlayer(id=1, first_name="Ali"),
        players=[TelegramPlayer(id=1, first_name="Ali")],
        game_type=GameTypeId.XO,
        lang="fa",
    )
    manager = GameSessionManager(InMemoryGameSessionStorage(), timeout=60.0)
    notified: list[int] = []

    async def on_deleted(game_id: int, _session: GameSession) -> None:
        notified.append(game_id)

    manager.subscribe("session_deleted", on_deleted)
    game_id = await manager.push(session)
    await manager.delete(game_id)

    assert notified == []
    assert await manager.get(game_id) is None


@pytest.mark.asyncio
async def test_in_memory_cleanup_expires_stale_sessions() -> None:
    catalog = GameCatalogService()
    entry = catalog.get("fa", GameTypeId.XO)
    session = GameSession(
        game_engine=create_engine(entry),
        inline_message_id="inline-stale",
        current_player=TelegramPlayer(id=2, first_name="Sara"),
        players=[TelegramPlayer(id=2, first_name="Sara")],
        game_type=GameTypeId.XO,
        lang="fa",
    )
    manager = GameSessionManager(InMemoryGameSessionStorage(), timeout=1.0)
    notified: list[int] = []

    async def on_deleted(game_id: int, _session: GameSession) -> None:
        notified.append(game_id)

    manager.subscribe("session_deleted", on_deleted)
    game_id = await manager.push(session)
    manager._last_accessed[game_id] = 0.0

    expired_ids = await manager.collect_expired_session_ids(limit=10)
    assert game_id in expired_ids

    for expired_id in expired_ids:
        await manager.expire(expired_id)

    assert notified == [game_id]
    assert await manager.get(game_id) is None


@pytest.mark.asyncio
async def test_expiry_index_pop_due() -> None:
    redis = AsyncMock()
    redis.zrangebyscore = AsyncMock(return_value=[b"101", b"202"])
    redis.zrem = AsyncMock(side_effect=[1, 1])

    index = SessionExpiryIndex(redis)
    await index.schedule(101, expires_at=time.time() + 30)
    redis.zadd.assert_awaited_once()

    due = await index.pop_due(limit=5)
    assert due == [101, 202]
    redis.zrangebyscore.assert_awaited_once()
