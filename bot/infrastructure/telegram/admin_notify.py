from __future__ import annotations

import logging
import traceback
from contextlib import suppress
from html import escape

from aiogram import Bot
from aiogram.types import Update

logger = logging.getLogger(__name__)

_MAX_MESSAGE_LEN = 4000


def _update_type(update: Update) -> str:
    with suppress(Exception):
        return update.event_type
    return "unknown"


def format_exception_message(exc: BaseException, *, update: Update | None = None) -> str:
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    lines = ["<b>Bot error</b>", f"<pre>{escape(tb[-3000:])}</pre>"]
    if update is not None:
        lines.insert(1, f"Update: <code>{escape(str(update.update_id))}</code>")
        lines.insert(2, f"Type: <code>{escape(_update_type(update))}</code>")
    text = "\n".join(lines)
    return text[:_MAX_MESSAGE_LEN]


async def notify_admins(bot: Bot, admin_ids: list[int], text: str) -> None:
    if not admin_ids:
        logger.warning("No ADMIN_IDS configured; skipping admin notification")
        return
    for admin_id in admin_ids:
        with suppress(Exception):
            await bot.send_message(admin_id, text)


async def answer_update_on_error(update: Update, *, alert_text: str = "Something went wrong.") -> None:
    if update.callback_query is not None:
        with suppress(Exception):
            await update.callback_query.answer(alert_text, show_alert=True)
    elif update.inline_query is not None:
        with suppress(Exception):
            await update.inline_query.answer([], cache_time=1, is_personal=True)
