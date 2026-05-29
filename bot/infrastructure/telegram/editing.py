from __future__ import annotations

from collections.abc import Awaitable

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

EMPTY_INLINE_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=[])


async def edit_callback_message(
    callback: CallbackQuery,
    *,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = EMPTY_INLINE_KEYBOARD,
) -> bool:
    """Edit the message attached to a callback query button."""
    if callback.bot is None:
        return False

    if callback.inline_message_id and await _try_edit(
        callback.bot.edit_message_text(
            inline_message_id=callback.inline_message_id,
            text=text,
            reply_markup=reply_markup,
        )
    ):
        return True

    message = callback.message
    if isinstance(message, Message):
        return await _try_edit(
            callback.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=message.message_id,
                text=text,
                reply_markup=reply_markup,
            )
        )

    return False


async def _try_edit[T](awaitable: Awaitable[T]) -> bool:
    try:
        await awaitable
    except TelegramBadRequest as exc:
        if "message is not modified" in str(exc).lower():
            return True
        raise
    else:
        return True
