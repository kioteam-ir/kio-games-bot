from __future__ import annotations

from contextlib import suppress
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, TelegramObject

from bot.infrastructure.idempotency.store import IdempotencyStore


class CallbackIdempotencyMiddleware(BaseMiddleware):
    def __init__(self, store: IdempotencyStore, *, ttl_seconds: int) -> None:
        self._store = store
        self._ttl_seconds = ttl_seconds

    async def __call__(
        self,
        handler: Any,
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, CallbackQuery):
            return await handler(event, data)

        key = f"callback:{event.id}"
        acquired = await self._store.acquire(key, ttl_seconds=self._ttl_seconds)
        if not acquired:
            with suppress(Exception):
                await event.answer()
            return None
        return await handler(event, data)
