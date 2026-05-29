from __future__ import annotations

from contextlib import suppress

from aiogram.types import CallbackQuery


async def answer_callback(
    callback: CallbackQuery,
    text: str | None = None,
    *,
    show_alert: bool = False,
) -> None:
    with suppress(Exception):
        await callback.answer(text or "", show_alert=show_alert and bool(text))
