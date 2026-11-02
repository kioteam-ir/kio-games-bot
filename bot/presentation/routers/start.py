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
async def start_handler(
    message: Message,
    user_context: ResolvedUserContext,
    keyboards: KeyboardService,
) -> None:
    await message.answer(
        _(I18nKeys.START),
        reply_markup=keyboards.start_keyboard(user_context.lang),
    )


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
    Command("add_sps"),
    ResolvedUserFilter(),
)
async def add_sponsor_handler(
    message: Message,
    command: CommandObject,
    container: AppContainer,
    user_context: ResolvedUserContext,
) -> None:
    if message.from_user is None or message.bot is None:
        return
    if message.from_user.id not in container.bot_config.admin_ids:
        return

    raw_args = (command.args or "").strip()
    if not raw_args:
        await message.answer(
            "➕ <b>افزودن اسپانسر جدید</b>\n\n"
            "راهنما: <code>/add_sps &lt;یوزرنیم یا لینک کانال یا شناسه&gt; [نام دلخواه]</code>\n\n"
            "مثال‌ها:\n"
            "• <code>/add_sps @kiogame</code>\n"
            "• <code>/add_sps https://t.me/kiogame کایو گیم</code>\n"
            "• <code>/add_sps -1004239396267 کایو گیم</code>\n\n"
            "<i>نکته: ربات حتماً باید در کانال عضو و ادمین باشد.</i>"
        )
        return

    parts = raw_args.split(maxsplit=1)
    target = parts[0].strip()
    custom_name = parts[1].strip() if len(parts) > 1 else None

    chat_identifier: str | int = target
    link = target
    for prefix in ("https://t.me/", "http://t.me/", "t.me/", "telegram.me/"):
        if target.startswith(prefix):
            uname = target.removeprefix(prefix).strip("/").split("/")[0].split("?")[0]
            if not uname.startswith("+"):
                chat_identifier = f"@{uname}"
                link = f"https://t.me/{uname}"
            break
    if isinstance(chat_identifier, str) and chat_identifier.startswith("@"):
        link = f"https://t.me/{chat_identifier[1:]}"
    elif isinstance(chat_identifier, str):
        try:
            chat_identifier = int(target)
        except ValueError:
            pass

    try:
        chat = await message.bot.get_chat(chat_identifier)
    except Exception as exc:
        await message.answer(
            f"❌ دریافت اطلاعات کانال از تلگرام با خطا مواجه شد:\n<code>{exc}</code>\n\n"
            "لطفاً مطمئن شوید ربات در کانال عضو و ادمین است."
        )
        return

    from aiogram.enums import ChatMemberStatus
    try:
        bot_member = await message.bot.get_chat_member(chat.id, message.bot.id)
        if bot_member.status not in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR}:
            await message.answer(
                f"⚠️ ربات در کانال <b>{chat.title}</b> ادمین نیست!\n"
                "برای اینکه بررسی عضویت کاربران در لحظه کار کند، ربات حتماً باید ادمین کانال باشد."
            )
            return
    except Exception:
        pass

    final_name = custom_name or chat.title or str(chat.id)
    final_link = chat.invite_link or link

    from api.infrastructure.database.connection import session_scope
    from api.infrastructure.database.models import AppSponser

    async with session_scope() as session:
        existing = await session.get(AppSponser, chat.id)
        if existing is not None:
            existing.name = final_name
            existing.link = final_link
            existing.is_active = True
        else:
            session.add(
                AppSponser(
                    id=chat.id,
                    name=final_name,
                    link=final_link,
                    joined_memebers=0,
                    is_active=True,
                )
            )

    count = await container.refresh_sponsors()
    await message.answer(
        f"✅ کانال اسپانسر در لحظه ثبت و فعال شد!\n\n"
        f"• نام: <b>{final_name}</b>\n"
        f"• شناسه واقعی: <code>{chat.id}</code>\n"
        f"• لینک: {final_link}\n\n"
        f"تعداد اسپانسرهای فعال: <b>{count}</b>"
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
    if message.from_user is None or message.bot is None:
        return
    if message.from_user.id not in container.bot_config.admin_ids:
        return

    raw_args = (command.args or "").strip()
    if not raw_args:
        sponsors = await container.sponsor_repo.list_active()
        if not sponsors:
            await message.answer("⚠️ هیچ اسپانسر فعالی یافت نشد.\n\nراهنما: <code>/del_sps &lt;شناسه یا یوزرنیم&gt;</code>")
            return

        lines = ["📋 <b>لیست اسپانسرهای فعال:</b>"]
        for sp in sponsors:
            lines.append(f"• <b>{sp.name}</b>: <code>{sp.id}</code> ({sp.link})")
        lines.append("\nبرای حذف: <code>/del_sps &lt;شناسه یا یوزرنیم&gt;</code>")
        await message.answer("\n".join(lines))
        return

    sp_id: int | None = None
    try:
        sp_id = int(raw_args)
    except ValueError:
        uname = raw_args
        for prefix in ("https://t.me/", "http://t.me/", "t.me/", "telegram.me/"):
            if uname.startswith(prefix):
                uname = uname.removeprefix(prefix).strip("/").split("/")[0].split("?")[0]
                break
        if not uname.startswith("@") and not uname.startswith("+"):
            uname = f"@{uname}"
        try:
            chat = await message.bot.get_chat(uname)
            sp_id = chat.id
        except Exception:
            sp_id = None

    from api.infrastructure.database.connection import session_scope
    from api.infrastructure.database.models import AppSponser
    from sqlalchemy import select

    async with session_scope() as session:
        existing = None
        if sp_id is not None:
            existing = await session.get(AppSponser, sp_id)
        if existing is None:
            res = await session.execute(
                select(AppSponser).where(AppSponser.link.ilike(f"%{raw_args}%"))
            )
            existing = res.scalars().first()

        if existing is None:
            await message.answer(f"❌ اسپانسری با مشخصات <code>{raw_args}</code> در دیتابیس یافت نشد.")
            return

        name = existing.name
        deleted_id = existing.id
        await session.delete(existing)

    count = await container.refresh_sponsors()
    await message.answer(
        f"✅ اسپانسر <b>{name}</b> (<code>{deleted_id}</code>) با موفقیت حذف و کش در لحظه باطل شد.\nتعداد اسپانسرهای فعال: {count}"
    )
