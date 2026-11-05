from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime

from aiogram import Bot, F, Router
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from sqlalchemy import func, select

from api.infrastructure.database.connection import session_scope
from api.infrastructure.database.models import AppGame, AppSponser, AppUser
from bot.core.container import AppContainer
from bot.infrastructure.callback.payloads import AdminActionCallback
from bot.infrastructure.telegram.keyboards import KeyboardService
from bot.presentation.filters.user import AdminFilter

logger = logging.getLogger(__name__)

router = Router(name="admin")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


class AdminStates(StatesGroup):
    waiting_for_broadcast = State()
    confirm_broadcast = State()
    waiting_for_sponsor = State()


def _admin_menu_text() -> str:
    return (
        "👑 <b>پنل مدیریت کایو گیم</b>\n\n"
        "به پنل مدیریت خوش آمدید. لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    )


# ---------------------------------------------------------
# 1. Menu & Navigation
# ---------------------------------------------------------


@router.message(Command("admin", "panel"))
async def admin_panel_handler(
    message: Message,
    keyboards: KeyboardService,
    state: FSMContext,
) -> None:
    await state.clear()
    await message.answer(
        _admin_menu_text(),
        reply_markup=keyboards.admin_panel_keyboard(),
    )


@router.callback_query(AdminActionCallback.filter(F.action == "menu"))
async def admin_menu_callback_handler(
    callback: CallbackQuery,
    keyboards: KeyboardService,
    state: FSMContext,
) -> None:
    await state.clear()
    if callback.message and isinstance(callback.message, Message):
        await callback.message.edit_text(
            _admin_menu_text(),
            reply_markup=keyboards.admin_panel_keyboard(),
        )
    await callback.answer()


@router.callback_query(AdminActionCallback.filter(F.action == "close"))
async def admin_close_callback_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await state.clear()
    if callback.message and isinstance(callback.message, Message):
        await callback.message.delete()
    await callback.answer("پنل مدیریت بسته شد.")


# ---------------------------------------------------------
# 2. View Users & Stats
# ---------------------------------------------------------


@router.callback_query(AdminActionCallback.filter(F.action == "users"))
async def admin_users_callback_handler(
    callback: CallbackQuery,
    keyboards: KeyboardService,
) -> None:
    async with session_scope() as session:
        total_users = await session.scalar(select(func.count(AppUser.id))) or 0
        banned_users = (
            await session.scalar(
                select(func.count(AppUser.id)).where(AppUser.is_banned.is_(True))
            )
            or 0
        )
        total_games = await session.scalar(select(func.count(AppGame.id))) or 0
        total_sponsors = (
            await session.scalar(
                select(func.count(AppSponser.id)).where(AppSponser.is_active.is_(True))
            )
            or 0
        )

        recent_res = await session.execute(
            select(AppUser).order_by(AppUser.joined_time.desc()).limit(10)
        )
        recent_users = recent_res.scalars().all()

    lines = [
        "👥 <b>آمار کاربران و سیستم:</b>\n",
        f"• 👤 کل کاربران: <b>{total_users:,}</b>",
        f"• 🟢 کاربران فعال: <b>{total_users - banned_users:,}</b>",
        f"• 🚫 کاربران مسدود: <b>{banned_users:,}</b>",
        f"• 🎮 کل بازی‌های انجام‌شده: <b>{total_games:,}</b>",
        f"• 🎫 اسپانسرهای فعال: <b>{total_sponsors:,}</b>\n",
        "🕒 <b>۱۰ کاربر اخیراً ثبت‌نام کرده:</b>",
    ]

    for idx, u in enumerate(recent_users, 1):
        uname = f"@{u.username}" if u.username and u.username != "WithOUtName" else "بدون یوزرنیم"
        joined = u.joined_time.strftime("%Y-%m-%d %H:%M") if u.joined_time else "-"
        lines.append(f"{idx}. <code>{u.id}</code> | {uname} ({joined})")

    text = "\n".join(lines)
    if callback.message and isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=keyboards.admin_users_keyboard())
    await callback.answer()


@router.callback_query(AdminActionCallback.filter(F.action == "export_users"))
async def admin_export_users_handler(
    callback: CallbackQuery,
    bot: Bot,
) -> None:
    await callback.answer("⏳ در حال استخراج لیست کاربران...")
    async with session_scope() as session:
        res = await session.execute(select(AppUser).order_by(AppUser.id.asc()))
        all_users = res.scalars().all()

    report_lines = [
        f"Kio Games Users Export - Generated at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"Total Users: {len(all_users)}",
        "=" * 70,
        "ID\tUSERNAME\tNAME\tLANG\tJOINED_TIME\tSTATUS",
        "=" * 70,
    ]

    for u in all_users:
        status = "BANNED" if u.is_banned else "ACTIVE"
        uname = u.username or "-"
        name = (u.name or "-").replace("\n", " ")
        joined = u.joined_time.strftime("%Y-%m-%d %H:%M:%S") if u.joined_time else "-"
        report_lines.append(f"{u.id}\t{uname}\t{name}\t{u.lang_code}\t{joined}\t{status}")

    file_content = "\n".join(report_lines).encode("utf-8")
    doc = BufferedInputFile(file_content, filename=f"users_export_{int(time.time())}.txt")

    if callback.from_user:
        await bot.send_document(
            chat_id=callback.from_user.id,
            document=doc,
            caption=f"📋 فایل لیست کامل کاربران ({len(all_users)} کاربر)",
        )


# ---------------------------------------------------------
# 3. View & Manage Sponsors
# ---------------------------------------------------------


@router.callback_query(AdminActionCallback.filter(F.action == "sponsors"))
async def admin_sponsors_list_handler(
    callback: CallbackQuery,
    container: AppContainer,
    keyboards: KeyboardService,
) -> None:
    sponsors = await container.sponsor_repo.list_active()
    if not sponsors:
        text = "🎫 <b>لیست اسپانسرها:</b>\n\nدر حال حاضر هیچ کانال اسپانسری فعال نیست."
    else:
        lines = [f"🎫 <b>لیست اسپانسرهای فعال ({len(sponsors)} مورد):</b>\n"]
        for idx, sp in enumerate(sponsors, 1):
            lines.append(f"{idx}. <b>{sp.name}</b>\n   • شناسه: <code>{sp.id}</code>\n   • لینک: {sp.link}\n")
        lines.append("<i>جهت حذف هر کانال، روی دکمه حذف مربوط به آن در زیر کلیک کنید.</i>")
        text = "\n".join(lines)

    if callback.message and isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=keyboards.admin_sponsors_keyboard(sponsors))
    await callback.answer()


@router.callback_query(AdminActionCallback.filter(F.action == "del_sps"))
async def admin_del_sponsor_handler(
    callback: CallbackQuery,
    callback_data: AdminActionCallback,
    container: AppContainer,
    keyboards: KeyboardService,
) -> None:
    sp_id = callback_data.target_id
    if not sp_id:
        await callback.answer("شناسه اسپانسر نامعتبر است.", show_alert=True)
        return

    async with session_scope() as session:
        sp = await session.get(AppSponser, sp_id)
        if sp is not None:
            name = sp.name
            await session.delete(sp)
            await session.flush()
        else:
            name = str(sp_id)

    count = await container.refresh_sponsors()
    await callback.answer(f"✅ اسپانسر '{name}' حذف شد (فعال: {count})", show_alert=True)

    # Refresh the sponsor list view
    sponsors = await container.sponsor_repo.list_active()
    if not sponsors:
        text = "🎫 <b>لیست اسپانسرها:</b>\n\nدر حال حاضر هیچ کانال اسپانسری فعال نیست."
    else:
        lines = [f"🎫 <b>لیست اسپانسرهای فعال ({len(sponsors)} مورد):</b>\n"]
        for idx, s in enumerate(sponsors, 1):
            lines.append(f"{idx}. <b>{s.name}</b>\n   • شناسه: <code>{s.id}</code>\n   • لینک: {s.link}\n")
        lines.append("<i>جهت حذف هر کانال، روی دکمه حذف مربوط به آن در زیر کلیک کنید.</i>")
        text = "\n".join(lines)

    if callback.message and isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=keyboards.admin_sponsors_keyboard(sponsors))


@router.callback_query(AdminActionCallback.filter(F.action == "refresh_sps"))
async def admin_refresh_sponsors_handler(
    callback: CallbackQuery,
    container: AppContainer,
) -> None:
    count = await container.refresh_sponsors()
    await callback.answer(f"🔄 کش اسپانسرها با موفقیت بروزرسانی شد! (تعداد فعال: {count})", show_alert=True)


# ---------------------------------------------------------
# 4. Add Sponsor via FSM
# ---------------------------------------------------------


@router.callback_query(AdminActionCallback.filter(F.action == "add_sps"))
async def admin_start_add_sponsor_handler(
    callback: CallbackQuery,
    keyboards: KeyboardService,
    state: FSMContext,
) -> None:
    await state.set_state(AdminStates.waiting_for_sponsor)
    text = (
        "➕ <b>افزودن کانال اسپانسر جدید</b>\n\n"
        "لطفاً یوزرنیم، لینک یا شناسه عددی کانال را ارسال فرمایید.\n"
        "همچنین می‌توانید نام دلخواه را با فاصله بعد از آن بنویسید.\n\n"
        "<b>مثال‌ها:</b>\n"
        "• <code>@kiogame</code>\n"
        "• <code>https://t.me/kiogame کایو گیم</code>\n"
        "• <code>-1004239396267</code>\n\n"
        "<i>نکته: ربات حتماً باید از قبل در کانال عضو و ادمین باشد.</i>"
    )
    if callback.message and isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=keyboards.admin_cancel_keyboard(back_to="sponsors"))
    await callback.answer()


@router.message(AdminStates.waiting_for_sponsor)
async def admin_receive_sponsor_handler(
    message: Message,
    bot: Bot,
    container: AppContainer,
    keyboards: KeyboardService,
    state: FSMContext,
) -> None:
    raw_args = (message.text or "").strip()
    if not raw_args:
        await message.answer("لطفاً یک متن معتبر حاوی لینک یا یوزرنیم کانال ارسال کنید.")
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
        chat = await bot.get_chat(chat_identifier)
    except Exception as exc:
        await message.answer(
            f"❌ دریافت اطلاعات کانال از تلگرام با خطا مواجه شد:\n<code>{exc}</code>\n\n"
            "لطفاً مطمئن شوید ربات در کانال عضو و ادمین است، سپس دوباره ارسال فرمایید.",
            reply_markup=keyboards.admin_cancel_keyboard(back_to="sponsors"),
        )
        return

    try:
        bot_member = await bot.get_chat_member(chat.id, bot.id)
        if bot_member.status not in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR}:
            await message.answer(
                f"⚠️ ربات در کانال <b>{chat.title}</b> ادمین نیست!\n"
                "برای اینکه بررسی عضویت کاربران در لحظه کار کند، ربات حتماً باید ادمین کانال باشد.\n"
                "ربات را ادمین کرده و دوباره تلاش کنید.",
                reply_markup=keyboards.admin_cancel_keyboard(back_to="sponsors"),
            )
            return
    except Exception:
        pass

    final_name = custom_name or chat.title or str(chat.id)
    final_link = chat.invite_link or link

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
    await state.clear()
    await message.answer(
        f"✅ کانال اسپانسر با موفقیت ثبت و فعال شد!\n\n"
        f"• نام: <b>{final_name}</b>\n"
        f"• شناسه: <code>{chat.id}</code>\n"
        f"• لینک: {final_link}\n\n"
        f"تعداد کل اسپانسرهای فعال: <b>{count}</b>",
        reply_markup=keyboards.admin_panel_keyboard(),
    )


# ---------------------------------------------------------
# 5. Broadcast to All Users (FSM)
# ---------------------------------------------------------


PRESET_CHALLENGE_TEXT = (
    "🎮 <b>حوصله‌ات سر رفته؟ وقتشه دوستات رو به چالش بکشی!</b>\n\n"
    "یه بازی دونفره، یه رقیب سرسخت و کلی لحظه هیجان‌انگیز! 🔥\n\n"
    "فرقی نمیکنه کی باشه؛ رفیق صمیمیت، همکارت یا حتی کسی که فکر میکنه همیشه برنده‌ست! 😏\n\n"
    "👥 دوستت رو انتخاب کن، یه بازی راه بنداز و ببین واقعاً کی حرفه‌ای‌تره!\n\n"
    "🏆 <b>شاید وقتشه رکورد رفیقات رو بزنی!</b>\n\n"
    "👇 همین الان برای دوستت بازی رو بفرست و یه بازی شروع کن!"
)


@router.callback_query(AdminActionCallback.filter(F.action == "broadcast"))
async def admin_start_broadcast_handler(
    callback: CallbackQuery,
    keyboards: KeyboardService,
    state: FSMContext,
) -> None:
    await state.set_state(AdminStates.waiting_for_broadcast)
    text = (
        "📢 <b>ارسال پیام به تمام کاربران (پیام همگانی)</b>\n\n"
        "لطفاً پیامی که مایلید برای تمام کاربران ارسال شود را در همین چت بفرستید، "
        "یا روی دکمه زیر بزنید تا از متن آماده «چالش دوستان» استفاده شود.\n\n"
        "<i>انواع محتوا شامل متن، عکس، ویدیو، گیف، فایل صوتی، استیکر و پیام‌های فورواردی پذیرفته می‌شود.</i>"
    )
    if callback.message and isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=keyboards.admin_broadcast_prompt_keyboard())
    await callback.answer()


@router.callback_query(AdminActionCallback.filter(F.action == "preset_bc"))
async def admin_preset_broadcast_handler(
    callback: CallbackQuery,
    keyboards: KeyboardService,
    state: FSMContext,
) -> None:
    if callback.message is None or not isinstance(callback.message, Message):
        await callback.answer()
        return

    preview_msg = await callback.message.answer(
        PRESET_CHALLENGE_TEXT,
        reply_markup=keyboards.start_keyboard("fa"),
    )
    await state.update_data(
        broadcast_msg_id=preview_msg.message_id,
        broadcast_chat_id=preview_msg.chat.id,
    )
    await state.set_state(AdminStates.confirm_broadcast)

    async with session_scope() as session:
        user_count = await session.scalar(select(func.count(AppUser.id))) or 0

    await preview_msg.reply(
        f"⚠️ <b>تایید ارسال پیام همگانی (متن آماده چالش)</b>\n\n"
        f"پیام بالا برای تمام <b>{user_count:,}</b> کاربر ربات ارسال خواهد شد.\n"
        "برای اینکه دکمه شیشه‌ای <b>«🎮 شروع بازی»</b> زیر پیام قرار گیرد، گزینه اول را انتخاب کنید:",
        reply_markup=keyboards.admin_confirm_broadcast_keyboard(),
    )
    await callback.answer()


@router.message(AdminStates.waiting_for_broadcast)
async def admin_receive_broadcast_message_handler(
    message: Message,
    keyboards: KeyboardService,
    state: FSMContext,
) -> None:
    await state.update_data(
        broadcast_msg_id=message.message_id,
        broadcast_chat_id=message.chat.id,
    )
    await state.set_state(AdminStates.confirm_broadcast)

    async with session_scope() as session:
        user_count = await session.scalar(select(func.count(AppUser.id))) or 0

    await message.reply(
        f"⚠️ <b>تایید ارسال پیام همگانی</b>\n\n"
        f"این پیام برای تمام <b>{user_count:,}</b> کاربر ربات ارسال خواهد شد.\n\n"
        "می‌توانید پیام را همراه با دکمه شیشه‌ای <b>«🎮 شروع بازی»</b> (انتخاب دوست/گروه و تایپ خودکار یوزرنیم بات) یا به صورت معمولی ارسال کنید:",
        reply_markup=keyboards.admin_confirm_broadcast_keyboard(),
    )


@router.callback_query(AdminActionCallback.filter(F.action == "cancel_bc"))
async def admin_cancel_broadcast_handler(
    callback: CallbackQuery,
    keyboards: KeyboardService,
    state: FSMContext,
) -> None:
    await state.clear()
    if callback.message and isinstance(callback.message, Message):
        await callback.message.edit_text(
            "❌ عملیات ارسال همگانی لغو شد.",
            reply_markup=keyboards.admin_panel_keyboard(),
        )
    await callback.answer("عملیات لغو شد.")


@router.callback_query(AdminActionCallback.filter(F.action.in_({"confirm_bc", "confirm_bc_btn"})))
async def admin_execute_broadcast_handler(
    callback: CallbackQuery,
    callback_data: AdminActionCallback,
    bot: Bot,
    keyboards: KeyboardService,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    msg_id = data.get("broadcast_msg_id")
    chat_id = data.get("broadcast_chat_id")
    await state.clear()

    if not msg_id or not chat_id:
        await callback.answer("پیام معتبری برای ارسال یافت نشد.", show_alert=True)
        return

    with_start_btn = callback_data.action == "confirm_bc_btn"

    await callback.answer("🚀 ارسال همگانی آغاز شد...")
    status_msg = None
    if callback.message and isinstance(callback.message, Message):
        status_msg = await callback.message.edit_text("⏳ <b>ارسال همگانی آغاز شد...</b>\nلطفاً شکیبا باشید.")

    async with session_scope() as session:
        res = await session.execute(
            select(AppUser.id, AppUser.lang_code).where(AppUser.is_banned.is_(False)).order_by(AppUser.id.asc())
        )
        users = [(row[0], row[1] or "fa") for row in res.all()]

    total = len(users)
    success = 0
    blocked = 0
    failed = 0
    start_time = time.monotonic()

    for idx, (uid, user_lang) in enumerate(users, 1):
        markup = keyboards.start_keyboard(user_lang) if with_start_btn else None
        try:
            await bot.copy_message(
                chat_id=uid,
                from_chat_id=chat_id,
                message_id=msg_id,
                reply_markup=markup,
            )
            success += 1
        except TelegramRetryAfter as retry:
            await asyncio.sleep(retry.retry_after)
            try:
                await bot.copy_message(
                    chat_id=uid,
                    from_chat_id=chat_id,
                    message_id=msg_id,
                    reply_markup=markup,
                )
                success += 1
            except Exception:
                failed += 1
        except TelegramForbiddenError:
            blocked += 1
        except Exception as exc:
            logger.debug("Failed sending broadcast to uid=%s: %s", uid, exc)
            failed += 1

        # Gentle throttle to stay well within Telegram limits (approx 25 msg/s)
        await asyncio.sleep(0.04)

        # Update progress every 50 users
        if status_msg and idx % 50 == 0:
            elapsed = time.monotonic() - start_time
            with asyncio.suppress(Exception):
                await status_msg.edit_text(
                    f"⏳ <b>در حال ارسال پیام همگانی...</b>\n\n"
                    f"• پیشرفت: <b>{idx}/{total}</b> ({(idx/total)*100:.1f}%)\n"
                    f"• موفق: <b>{success}</b>\n"
                    f"• مسدود: <b>{blocked}</b>\n"
                    f"• ناموفق: <b>{failed}</b>\n"
                    f"• زمان سپری‌شده: <b>{elapsed:.0f}s</b>"
                )

    total_time = time.monotonic() - start_time
    report = (
        "✅ <b>ارسال همگانی به پایان رسید!</b>\n\n"
        f"📊 <b>گزارش نهایی:</b>\n"
        f"• کل کاربران هدف: <b>{total:,}</b>\n"
        f"• با موفقیت ارسال شد: <b>{success:,}</b>\n"
        f"• مسدود کرده بودند: <b>{blocked:,}</b>\n"
        f"• ناموفق / خطا: <b>{failed:,}</b>\n"
        f"• مدت زمان کل: <b>{total_time:.1f} ثانیه</b>"
    )

    if status_msg:
        with asyncio.suppress(Exception):
            await status_msg.edit_text(report, reply_markup=keyboards.admin_panel_keyboard())
    elif callback.message and isinstance(callback.message, Message):
        await callback.message.answer(report, reply_markup=keyboards.admin_panel_keyboard())
