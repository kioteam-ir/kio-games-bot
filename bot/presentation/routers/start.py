from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import Message
from aiogram.utils.i18n import gettext as _

from bot.application.dto.game import ResolvedUserContext
from bot.core.container import AppContainer
from bot.infrastructure.telegram.keyboards import KeyboardService
from bot.locales.i18n_keys import I18nKeys
from bot.presentation.filters.sponsor import SponsorOkFilter, SponsorRequiredFilter
from bot.presentation.filters.user import NotBannedFilter, ResolvedUserFilter

router = Router(name="start")


@router.message(CommandStart(), ResolvedUserFilter(), NotBannedFilter(), SponsorRequiredFilter())
async def start_sponsor_gate_handler(
    message: Message,
    join_message: str | None = None,
    sponsors: list[object] | None = None,
    keyboards: KeyboardService | None = None,
) -> None:
    from bot.domain.schemas.sponsor import SponsorRecord

    if join_message is None or keyboards is None:
        return
    sponsor_rows = [s for s in (sponsors or []) if isinstance(s, SponsorRecord)]
    await message.answer(
        join_message,
        reply_markup=keyboards.sponsor_keyboard(sponsor_rows),
    )


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


@router.message(
    Command("del_sps", "remove_sps"),
    ResolvedUserFilter(),
)
async def remove_sponsor_handler(
    message: Message,
    command: CommandObject,
    container: AppContainer,
    user_context: ResolvedUserContext,
) -> None:
    if message.from_user is None:
        return
    if message.from_user.id not in container.bot_config.admin_ids:
        return

    raw_args = (command.args or "").strip()
    if not raw_args:
        sponsors = await container.sponsor_repo.list_active()
        if not sponsors:
            await message.answer("⚠️ هیچ اسپانسر فعالی یافت نشد.\n\nراهنما: <code>/del_sps &lt;channel_id&gt;</code>")
            return

        lines = ["📋 <b>لیست اسپانسرهای فعال:</b>"]
        for sp in sponsors:
            lines.append(f"• <b>{sp.name}</b>: <code>{sp.id}</code>")
        lines.append("\nبرای حذف: <code>/del_sps &lt;channel_id&gt;</code>")
        await message.answer("\n".join(lines))
        return

    try:
        sp_id = int(raw_args)
    except ValueError:
        await message.answer("❌ شناسه کانال نامعتبر است. شناسه باید عدد باشد.\nمثال: <code>/del_sps -1001234567890</code>")
        return

    from api.infrastructure.database.connection import session_scope
    from api.infrastructure.database.models import AppSponser

    async with session_scope() as session:
        existing = await session.get(AppSponser, sp_id)
        if existing is None:
            await message.answer(f"❌ اسپانسری با شناسه <code>{sp_id}</code> در دیتابیس یافت نشد.")
            return

        name = existing.name
        await session.delete(existing)

    count = await container.refresh_sponsors()
    await message.answer(
        f"✅ اسپانسر <b>{name}</b> (<code>{sp_id}</code>) با موفقیت حذف شد.\nتعداد اسپانسرهای فعال: {count}"
    )
