from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Chat, Message, User

from bot.infrastructure.telegram.editing import EMPTY_INLINE_KEYBOARD, edit_callback_message


def _user() -> User:
    return User(id=1, is_bot=False, first_name="Test")


@pytest.mark.asyncio
async def test_edit_callback_message_uses_inline_message_id() -> None:
    bot = AsyncMock()
    callback = CallbackQuery(
        id="1",
        from_user=_user(),
        chat_instance="abc",
        inline_message_id="inline-123",
    )
    callback._bot = bot

    edited = await edit_callback_message(callback, text="Hello")

    assert edited is True
    bot.edit_message_text.assert_awaited_once_with(
        inline_message_id="inline-123",
        text="Hello",
        reply_markup=EMPTY_INLINE_KEYBOARD,
    )


@pytest.mark.asyncio
async def test_edit_callback_message_falls_back_to_chat_message() -> None:
    bot = AsyncMock()
    message = Message(
        message_id=42,
        date=datetime.now(tz=UTC),
        chat=Chat(id=7, type="private"),
    )
    callback = CallbackQuery(
        id="2",
        from_user=_user(),
        chat_instance="abc",
        message=message,
    )
    callback._bot = bot

    edited = await edit_callback_message(callback, text="Updated")

    assert edited is True
    bot.edit_message_text.assert_awaited_once_with(
        chat_id=7,
        message_id=42,
        text="Updated",
        reply_markup=EMPTY_INLINE_KEYBOARD,
    )


@pytest.mark.asyncio
async def test_edit_callback_message_treats_not_modified_as_success() -> None:
    bot = AsyncMock()
    bot.edit_message_text.side_effect = TelegramBadRequest(
        method=AsyncMock(),
        message="Bad Request: message is not modified",
    )
    callback = CallbackQuery(
        id="3",
        from_user=_user(),
        chat_instance="abc",
        inline_message_id="inline-456",
    )
    callback._bot = bot

    edited = await edit_callback_message(callback, text="Same")

    assert edited is True
