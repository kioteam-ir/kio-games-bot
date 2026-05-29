from __future__ import annotations

import pytest
from aiogram.types import CallbackQuery, Chat, Message, User

from bot.infrastructure.idempotency.store import InMemoryIdempotencyStore
from bot.presentation.middlewares.idempotency import CallbackIdempotencyMiddleware


@pytest.mark.asyncio
async def test_idempotency_middleware_blocks_duplicate_callback() -> None:
    store = InMemoryIdempotencyStore()
    middleware = CallbackIdempotencyMiddleware(store, ttl_seconds=60)
    calls = {"count": 0}

    async def handler(_event: CallbackQuery, _data: dict[str, object]) -> str:
        calls["count"] += 1
        return "handled"

    user = User(id=1, is_bot=False, first_name="Alice")
    chat = Chat(id=1, type="private")
    message = Message(message_id=1, date=0, chat=chat, from_user=user)
    callback = CallbackQuery(id="cb-1", from_user=user, chat_instance="x", message=message)

    first = await middleware(handler, callback, {})
    second = await middleware(handler, callback, {})

    assert first == "handled"
    assert second is None
    assert calls["count"] == 1


@pytest.mark.asyncio
async def test_idempotency_store_allows_different_keys() -> None:
    store = InMemoryIdempotencyStore()
    assert await store.acquire("a", ttl_seconds=60) is True
    assert await store.acquire("a", ttl_seconds=60) is False
    assert await store.acquire("b", ttl_seconds=60) is True
