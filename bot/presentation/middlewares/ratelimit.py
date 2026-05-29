from __future__ import annotations

from contextlib import suppress
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, InlineQuery, Message, TelegramObject

from bot.config.ratelimit import RateLimitConfigClass, RateLimitRule
from bot.infrastructure.callback.parsing import parse_make_game_callback
from bot.infrastructure.callback.payloads import CellMoveCallback, JoinGameCallback
from bot.infrastructure.i18n.translator import Translator
from bot.infrastructure.ratelimit.service import RateLimitService
from bot.locales.i18n_keys import I18nKeys


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, service: RateLimitService, config: RateLimitConfigClass) -> None:
        self._service = service
        self._config = config

    async def __call__(
        self,
        handler: Any,
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not self._service.enabled:
            return await handler(event, data)

        user_id = _extract_user_id(event)
        if user_id is None:
            return await handler(event, data)

        scope, rule = _resolve_scope(event, self._config)
        if scope is None or rule is None:
            return await handler(event, data)

        if await self._service.allow(scope, user_id, rule):
            return await handler(event, data)

        await _notify_rate_limited(event, data)
        return None


def _extract_user_id(event: TelegramObject) -> int | None:
    from_user = getattr(event, "from_user", None)
    if from_user is None:
        return None
    return from_user.id


def _resolve_scope(event: TelegramObject, config: RateLimitConfigClass) -> tuple[str | None, RateLimitRule | None]:
    if isinstance(event, InlineQuery):
        return "inline_query", config.inline_query
    if isinstance(event, Message):
        return "message", config.message
    if isinstance(event, CallbackQuery) and event.data:
        return _resolve_callback_scope(event.data, config)
    if isinstance(event, CallbackQuery):
        return "callback:default", config.callback_default
    return None, None


def _resolve_callback_scope(data: str, config: RateLimitConfigClass) -> tuple[str, RateLimitRule]:
    if parse_make_game_callback(data) is not None:
        return "callback:create", config.callback_create
    for callback_type, scope, rule in (
        (JoinGameCallback, "callback:join", config.callback_join),
        (CellMoveCallback, "callback:move", config.callback_move),
    ):
        with suppress(ValueError, TypeError):
            callback_type.unpack(data)
            return scope, rule
    return "callback:default", config.callback_default


async def _notify_rate_limited(event: TelegramObject, data: dict[str, Any]) -> None:
    translator = data.get("translator")
    locale = data.get("locale", "fa")
    message = "Too many requests. Please wait."
    if isinstance(translator, Translator) and isinstance(locale, str):
        message = translator.t(I18nKeys.RATE_LIMIT_EXCEEDED, locale)

    if isinstance(event, CallbackQuery):
        with suppress(Exception):
            await event.answer(message, show_alert=False)
        return
    if isinstance(event, InlineQuery):
        with suppress(Exception):
            await event.answer([], cache_time=1, is_personal=True)
        return
    if isinstance(event, Message):
        with suppress(Exception):
            await event.answer(message)
