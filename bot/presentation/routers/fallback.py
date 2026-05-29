from __future__ import annotations

import logging

from aiogram import Bot, Router
from aiogram.types import (
    CallbackQuery,
    ChosenInlineResult,
    ErrorEvent,
    InlineQuery,
    Message,
)

from bot.core.container import AppContainer
from bot.infrastructure.telegram.admin_notify import (
    answer_update_on_error,
    format_exception_message,
    notify_admins,
)

logger = logging.getLogger(__name__)

catch_all_router = Router(name="catch_all")


def register_error_handler(router: Router) -> None:
    @router.errors()
    async def on_error(event: ErrorEvent, bot: Bot, container: AppContainer) -> None:
        update = event.update
        logger.exception(
            "Unhandled exception in update %s",
            update.update_id,
            exc_info=event.exception,
        )
        text = format_exception_message(event.exception, update=update)
        await notify_admins(bot, container.bot_config.admin_ids, text)
        await answer_update_on_error(update)


@catch_all_router.message()
async def catch_all_message(message: Message) -> None:
    logger.info(
        "Unhandled message update_id=%s user_id=%s text=%r",
        message.message_id,
        message.from_user.id if message.from_user else None,
        message.text,
    )


@catch_all_router.callback_query()
async def catch_all_callback(callback: CallbackQuery) -> None:
    logger.info(
        "Unhandled callback update_id=%s user_id=%s data=%r",
        callback.id,
        callback.from_user.id if callback.from_user else None,
        callback.data,
    )
    await callback.answer()


@catch_all_router.inline_query()
async def catch_all_inline_query(inline_query: InlineQuery) -> None:
    logger.info(
        "Unhandled inline_query user_id=%s query=%r",
        inline_query.from_user.id if inline_query.from_user else None,
        inline_query.query,
    )
    await inline_query.answer([], cache_time=1, is_personal=True)


@catch_all_router.chosen_inline_result()
async def catch_all_chosen_inline_result(chosen: ChosenInlineResult) -> None:
    logger.info(
        "Unhandled chosen_inline_result user_id=%s result_id=%r",
        chosen.from_user.id if chosen.from_user else None,
        chosen.result_id,
    )
