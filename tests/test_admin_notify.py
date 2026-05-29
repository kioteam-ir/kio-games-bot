from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from aiogram.types import Update

from bot.infrastructure.telegram.admin_notify import format_exception_message, notify_admins


def test_format_exception_message_includes_update_metadata() -> None:
    update = Update.model_construct(update_id=42, message=None)
    text = format_exception_message(RuntimeError("boom"), update=update)

    assert "Bot error" in text
    assert "RuntimeError" in text
    assert "boom" in text
    assert "42" in text


@pytest.mark.asyncio
async def test_notify_admins_sends_to_each_admin() -> None:
    bot = AsyncMock()

    await notify_admins(bot, [111, 222], "hello")

    assert bot.send_message.await_count == 2
    bot.send_message.assert_any_await(111, "hello")
    bot.send_message.assert_any_await(222, "hello")


@pytest.mark.asyncio
async def test_notify_admins_skips_when_empty() -> None:
    bot = AsyncMock()

    await notify_admins(bot, [], "hello")

    bot.send_message.assert_not_awaited()
