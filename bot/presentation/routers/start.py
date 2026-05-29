from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from bot.domain.schemas.texts import CommandKey
from bot.infrastructure.i18n.texts import TextsService
from bot.presentation.filters.sponsor import SponsorOkFilter
from bot.presentation.filters.user import NotBannedFilter, ResolvedUserFilter

router = Router(name="start")


@router.message(CommandStart(), ResolvedUserFilter(), NotBannedFilter(), SponsorOkFilter())
async def start_handler(message: Message, texts: TextsService, user_context: object) -> None:
    from bot.application.dto.game import ResolvedUserContext

    if not isinstance(user_context, ResolvedUserContext):
        return
    await message.answer(texts.get(user_context.lang, CommandKey.START))


@router.message(
    Command("update_sps"),
    ResolvedUserFilter(),
)
async def update_sponsors_handler(
    message: Message,
    container: object,
) -> None:
    from bot.core.container import AppContainer

    if not isinstance(container, AppContainer) or message.from_user is None:
        return
    if message.from_user.id not in container.bot_config.admin_ids:
        return
    count = await container.refresh_sponsors()
    await message.answer(f"sponsors updated: {count}")
