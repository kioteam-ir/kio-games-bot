from __future__ import annotations

import logging
from contextlib import suppress

from aiogram import Bot, Router
from aiogram.types import CallbackQuery, ErrorEvent, InlineQuery, Message, Update

from bot.core.container import AppContainer
from bot.infrastructure.callback.parsing import parse_make_game_callback
from bot.infrastructure.callback.payloads import (
    CellMoveCallback,
    ChangeLangCallback,
    JoinGameCallback,
    PlayerInfoCallback,
)
from bot.infrastructure.i18n.translator import Translator
from bot.infrastructure.telegram.admin_notify import (
    answer_update_on_error,
    format_exception_message,
    notify_admins,
)
from bot.infrastructure.telegram.callbacks import answer_callback
from bot.locales.i18n_keys import I18nKeys

logger = logging.getLogger(__name__)

catch_all_router = Router(name="catch_all")


def register_error_handler(router: Router) -> None:
    @router.errors()
    async def on_error(event: ErrorEvent, bot: Bot, container: AppContainer) -> None:
        update = event.update
        logger.exception(
            "Exception in update %s",
            update.update_id,
            exc_info=event.exception,
        )
        text = format_exception_message(event.exception, update=update)
        await notify_admins(bot, container.bot_config.admin_ids, text)
        await answer_update_on_error(update)


@catch_all_router.update()
async def fallback_update(
    update: Update,
    translator: Translator | None = None,
    locale: str = "fa",
) -> None:
    if update.callback_query is not None:
        await _fallback_callback(update.callback_query, translator, locale)
        return
    if update.inline_query is not None:
        await _fallback_inline_query(update.inline_query)
        return
    if update.chosen_inline_result is not None:
        return
    if update.message is not None:
        await _fallback_message(update.message, translator, locale)
        return
    if update.edited_message is not None:
        return
    logger.debug("Fallback acknowledged update_id=%s type=%s", update.update_id, update.event_type)


async def _fallback_callback(
    callback: CallbackQuery,
    translator: Translator | None,
    locale: str,
) -> None:
    data = callback.data or ""
    message = _callback_fallback_message(data, callback, translator, locale)
    await answer_callback(callback, message, show_alert=bool(message))
    logger.debug(
        "Fallback callback user_id=%s data=%r",
        callback.from_user.id if callback.from_user else None,
        data,
    )


async def _fallback_inline_query(inline_query: InlineQuery) -> None:
    with suppress(Exception):
        await inline_query.answer([], cache_time=1, is_personal=True)
    logger.debug(
        "Fallback inline_query user_id=%s query=%r",
        inline_query.from_user.id if inline_query.from_user else None,
        inline_query.query,
    )


async def _fallback_message(
    message: Message,
    translator: Translator | None,
    locale: str,
) -> None:
    if message.from_user is None:
        return
    text = translator.t(I18nKeys.START, locale) if translator else I18nKeys.START.value
    with suppress(Exception):
        await message.answer(text)
    logger.debug(
        "Fallback message user_id=%s text=%r",
        message.from_user.id,
        message.text,
    )


def _callback_fallback_message(
    data: str,
    callback: CallbackQuery,
    translator: Translator | None,
    locale: str,
) -> str | None:
    if translator is None:
        return None

    make_game = parse_make_game_callback(data)
    if make_game is not None:
        if callback.from_user is not None and callback.from_user.id != make_game.creator_id:
            return translator.t(I18nKeys.NOT_YOUR_GAME, locale)
        return translator.t(I18nKeys.JOIN_FIRST, locale)

    for payload_cls in (JoinGameCallback, CellMoveCallback, ChangeLangCallback, PlayerInfoCallback):
        with suppress(ValueError, TypeError):
            payload_cls.unpack(data)
            return translator.t(I18nKeys.NOT_YOUR_GAME, locale)

    return None
