from __future__ import annotations

import logging
from contextlib import suppress

from aiogram import Bot, Router
from aiogram.types import (
    CallbackQuery,
    ChatJoinRequest,
    ChatMemberUpdated,
    ChosenInlineResult,
    ErrorEvent,
    InlineQuery,
    Message,
    Poll,
    PollAnswer,
    PreCheckoutQuery,
    ShippingQuery,
)

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


@catch_all_router.callback_query()
async def catch_all_callback(
    callback: CallbackQuery,
    translator: Translator | None = None,
    locale: str = "fa",
) -> None:
    data = callback.data or ""
    message = _callback_fallback_message(data, callback, translator, locale)
    await answer_callback(callback, message, show_alert=bool(message))
    logger.debug(
        "Fallback callback user_id=%s data=%r",
        callback.from_user.id if callback.from_user else None,
        data,
    )


@catch_all_router.inline_query()
async def catch_all_inline_query(inline_query: InlineQuery) -> None:
    with suppress(Exception):
        await inline_query.answer([], cache_time=1, is_personal=True)
    logger.debug(
        "Fallback inline_query user_id=%s query=%r",
        inline_query.from_user.id if inline_query.from_user else None,
        inline_query.query,
    )


@catch_all_router.chosen_inline_result()
async def catch_all_chosen_inline_result(chosen: ChosenInlineResult) -> None:
    logger.debug(
        "Fallback chosen_inline_result user_id=%s result_id=%r",
        chosen.from_user.id if chosen.from_user else None,
        chosen.result_id,
    )


@catch_all_router.message()
async def catch_all_message(
    message: Message,
    translator: Translator | None = None,
    locale: str = "fa",
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


@catch_all_router.edited_message()
async def catch_all_edited_message(message: Message) -> None:
    logger.debug(
        "Fallback edited_message user_id=%s",
        message.from_user.id if message.from_user else None,
    )


@catch_all_router.channel_post()
async def catch_all_channel_post(message: Message) -> None:
    logger.debug("Fallback channel_post chat_id=%s", message.chat.id)


@catch_all_router.edited_channel_post()
async def catch_all_edited_channel_post(message: Message) -> None:
    logger.debug("Fallback edited_channel_post chat_id=%s", message.chat.id)


@catch_all_router.poll()
async def catch_all_poll(poll: Poll) -> None:
    logger.debug("Fallback poll id=%s", poll.id)


@catch_all_router.poll_answer()
async def catch_all_poll_answer(poll_answer: PollAnswer) -> None:
    logger.debug(
        "Fallback poll_answer user_id=%s poll_id=%s",
        poll_answer.user.id,
        poll_answer.poll_id,
    )


@catch_all_router.my_chat_member()
async def catch_all_my_chat_member(event: ChatMemberUpdated) -> None:
    logger.debug("Fallback my_chat_member chat_id=%s", event.chat.id)


@catch_all_router.chat_member()
async def catch_all_chat_member(event: ChatMemberUpdated) -> None:
    logger.debug("Fallback chat_member chat_id=%s", event.chat.id)


@catch_all_router.chat_join_request()
async def catch_all_chat_join_request(request: ChatJoinRequest) -> None:
    logger.debug("Fallback chat_join_request chat_id=%s", request.chat.id)


@catch_all_router.pre_checkout_query()
async def catch_all_pre_checkout_query(query: PreCheckoutQuery) -> None:
    with suppress(Exception):
        await query.answer(ok=False, error_message="Unsupported")
    logger.debug("Fallback pre_checkout_query user_id=%s", query.from_user.id)


@catch_all_router.shipping_query()
async def catch_all_shipping_query(query: ShippingQuery) -> None:
    with suppress(Exception):
        await query.answer(ok=False, error_message="Unsupported")
    logger.debug("Fallback shipping_query user_id=%s", query.from_user.id)


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
