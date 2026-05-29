from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram.utils.i18n import gettext as _

from bot.application.dto.game import ResolvedUserContext
from bot.core.container import AppContainer
from bot.locales.i18n_keys import I18nKeys
from bot.presentation.filters.sponsor import SponsorOkFilter
from bot.presentation.filters.user import NotBannedFilter, ResolvedUserFilter

router = Router(name="start")


@router.message(CommandStart(), ResolvedUserFilter(), NotBannedFilter(), SponsorOkFilter())
async def start_handler(message: Message, user_context: ResolvedUserContext) -> None:
    await message.answer(_(I18nKeys.START))


@router.message(
    Command("update_sps"),
    ResolvedUserFilter(),
)
async def update_sponsors_handler(
    message: Message,
    container: AppContainer,
    user_context: ResolvedUserContext,
) -> None:
    if message.from_user is None:
        return
    if message.from_user.id not in container.bot_config.admin_ids:
        return
    count = await container.refresh_sponsors()
    await message.answer(
        container.translator.t(I18nKeys.SPONSORS_UPDATED, user_context.lang, count=count),
    )
