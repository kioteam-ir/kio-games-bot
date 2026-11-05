# ruff: noqa: E501
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, SwitchInlineQueryChosenChat

from bot.application.dto.board import BoardState
from bot.application.dto.game import GameBoardView
from bot.domain.schemas.game import GameTypeId
from bot.domain.schemas.sponsor import SponsorRecord
from bot.infrastructure.callback.service import CallbackService
from bot.infrastructure.i18n.translator import Translator
from bot.locales.i18n_keys import I18nKeys

LANGUAGE_OPTIONS: list[tuple[str, str]] = [
    ("tr", "🇹🇷 Türkçe 🇹🇷"),
    ("en", "🇺🇸 English 🇺🇸"),
    ("fa", "🇮🇷 فارسی 🇮🇷"),
    ("ru", "🇷🇺 Русский 🇷🇺"),
    ("de", "🇩🇪 Deutsch 🇩🇪"),
    ("fr", "🇫🇷 Français 🇫🇷"),
    ("ar", "🇸🇦 العربية 🇸🇦"),
    ("he", "🇮🇱 עברית 🇮🇱"),
    ("zh", "🇨🇳 中文 🇨🇳"),
    ("ku", "🏳️ کوردی 🏳️"),
    ("hi", "🇮🇳 हिन्दी 🇮🇳"),
    ("ps", "🇦🇫 پښتو 🇦🇫"),
]


class KeyboardService:
    def __init__(self, translator: Translator, bot_username: str) -> None:
        self._translator = translator
        self._bot_username = bot_username

    def sponsor_keyboard(
        self,
        sponsors: list[SponsorRecord],
        *,
        extra_row: list[InlineKeyboardButton] | None = None,
    ) -> InlineKeyboardMarkup:
        rows = [[InlineKeyboardButton(text=f"🎫 {s.name.strip()} 🎫", url=str(s.link))] for s in sponsors]
        if extra_row:
            rows.insert(0, extra_row)
        return InlineKeyboardMarkup(inline_keyboard=rows)

    def start_game_button(self, lang: str = "fa") -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text=self._translator.t(I18nKeys.START_GAME_BUTTON, lang),
            switch_inline_query_chosen_chat=SwitchInlineQueryChosenChat(
                query="",
                allow_user_chats=True,
                allow_group_chats=True,
                allow_channel_chats=False,
                allow_bot_chats=False,
            ),
        )

    def start_keyboard(self, lang: str = "fa") -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [self.start_game_button(lang)],
            ]
        )

    def admin_panel_keyboard(self) -> InlineKeyboardMarkup:
        from bot.infrastructure.callback.payloads import AdminActionCallback

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📢 پیام به همه کاربران (چت همگانی)",
                        callback_data=AdminActionCallback(action="broadcast").pack(),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="👥 مشاهده کاربران و آمار",
                        callback_data=AdminActionCallback(action="users").pack(),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📋 لیست اسپانسرها",
                        callback_data=AdminActionCallback(action="sponsors").pack(),
                    ),
                    InlineKeyboardButton(
                        text="➕ افزودن اسپانسر",
                        callback_data=AdminActionCallback(action="add_sps").pack(),
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="🔄 بروزرسانی کش اسپانسرها",
                        callback_data=AdminActionCallback(action="refresh_sps").pack(),
                    ),
                    InlineKeyboardButton(
                        text="❌ بستن پنل",
                        callback_data=AdminActionCallback(action="close").pack(),
                    ),
                ],
            ]
        )

    def admin_users_keyboard(self) -> InlineKeyboardMarkup:
        from bot.infrastructure.callback.payloads import AdminActionCallback

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📥 دانلود لیست کامل کاربران (فایل TXT)",
                        callback_data=AdminActionCallback(action="export_users").pack(),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت به منوی ادمین",
                        callback_data=AdminActionCallback(action="menu").pack(),
                    )
                ],
            ]
        )

    def admin_sponsors_keyboard(self, sponsors: list[SponsorRecord]) -> InlineKeyboardMarkup:
        from bot.infrastructure.callback.payloads import AdminActionCallback

        rows: list[list[InlineKeyboardButton]] = []
        for s in sponsors:
            rows.append(
                [
                    InlineKeyboardButton(
                        text=f"🗑 حذف {s.name.strip()}",
                        callback_data=AdminActionCallback(action="del_sps", target_id=s.id).pack(),
                    )
                ]
            )
        rows.append(
            [
                InlineKeyboardButton(
                    text="➕ افزودن اسپانسر جدید",
                    callback_data=AdminActionCallback(action="add_sps").pack(),
                ),
                InlineKeyboardButton(
                    text="🔄 بروزرسانی کش",
                    callback_data=AdminActionCallback(action="refresh_sps").pack(),
                ),
            ]
        )
        rows.append(
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت به منوی ادمین",
                    callback_data=AdminActionCallback(action="menu").pack(),
                )
            ]
        )
        return InlineKeyboardMarkup(inline_keyboard=rows)

    def admin_broadcast_prompt_keyboard(self) -> InlineKeyboardMarkup:
        from bot.infrastructure.callback.payloads import AdminActionCallback

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔥 استفاده از متن آماده «چالش دوستان»",
                        callback_data=AdminActionCallback(action="preset_bc").pack(),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ لغو و بازگشت",
                        callback_data=AdminActionCallback(action="menu").pack(),
                    )
                ],
            ]
        )

    def admin_confirm_broadcast_keyboard(self) -> InlineKeyboardMarkup:
        from bot.infrastructure.callback.payloads import AdminActionCallback

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🎮 ارسال همراه با دکمه شیشه‌ای «شروع بازی»",
                        callback_data=AdminActionCallback(action="confirm_bc_btn").pack(),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="✅ ارسال معمولی (بدون دکمه اضافه)",
                        callback_data=AdminActionCallback(action="confirm_bc").pack(),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ لغو و انصراف",
                        callback_data=AdminActionCallback(action="cancel_bc").pack(),
                    )
                ],
            ]
        )

    def admin_cancel_keyboard(self, back_to: str = "menu") -> InlineKeyboardMarkup:
        from bot.infrastructure.callback.payloads import AdminActionCallback

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌ لغو و بازگشت",
                        callback_data=AdminActionCallback(action=back_to).pack(),
                    )
                ]
            ]
        )

    def waiting_keyboard(
        self,
        lang: str,
        game_id: int,
        sponsors: list[SponsorRecord] | None = None,
    ) -> InlineKeyboardMarkup:
        rows: list[list[InlineKeyboardButton]] = [
            [
                InlineKeyboardButton(
                    text=self._translator.t(I18nKeys.IPLAY, lang),
                    callback_data=CallbackService.build_join_game(game_id),
                )
            ]
        ]
        if sponsors:
            for s in sponsors:
                rows.append([InlineKeyboardButton(text=f"🎫 {s.name.strip()} 🎫", url=str(s.link))])
        return InlineKeyboardMarkup(inline_keyboard=rows)

    def mine_count_picker(self, lang: str, creator_id: int) -> InlineKeyboardMarkup:
        del lang
        rows: list[list[InlineKeyboardButton]] = [
            [
                InlineKeyboardButton(
                    text="9",
                    callback_data=CallbackService.build_make_game(creator_id, int(GameTypeId.MINE), mine_count=9),
                ),
                InlineKeyboardButton(
                    text="15",
                    callback_data=CallbackService.build_make_game(creator_id, int(GameTypeId.MINE), mine_count=15),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="5",
                    callback_data=CallbackService.build_make_game(creator_id, int(GameTypeId.MINE), mine_count=5),
                ),
            ],
        ]
        return InlineKeyboardMarkup(inline_keyboard=rows)

    def timeout_keyboard(self, lang: str) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=self._translator.t(I18nKeys.PLAY_WITH_COOL_PEOPLE_BUTTON, lang),
                        switch_inline_query=" ",
                    )
                ]
            ]
        )

    def game_board(self, view: GameBoardView) -> InlineKeyboardMarkup:
        return self._build_board(view.board)

    def _build_board(self, board: BoardState) -> InlineKeyboardMarkup:
        rows: list[list[InlineKeyboardButton]] = []
        active = not board.game_over
        bot_url = f"https://t.me/{self._bot_username}"

        for row in board.rows:
            buttons: list[InlineKeyboardButton] = []
            for cell in row:
                buttons.append(
                    InlineKeyboardButton(
                        text=cell.label,
                        callback_data=CallbackService.build_cell_move(cell.row, cell.col, board.game_id)
                        if active
                        else None,
                        url=None if active else bot_url,
                    )
                )
            rows.append(buttons)

        if board.column_picker is not None:
            move_row: list[InlineKeyboardButton] = []
            for option in board.column_picker:
                move_row.append(
                    InlineKeyboardButton(
                        text=option.label,
                        callback_data=CallbackService.build_cell_move(0, option.col, board.game_id) if active else None,
                        url=None if active else bot_url,
                    )
                )
            rows.append(move_row)

        if board.players:
            rows.append(
                [
                    InlineKeyboardButton(
                        text=f"🎮 {'🔺' if slot.is_current else ''} {slot.name}",
                        callback_data=CallbackService.build_player_info(
                            slot.player_id,
                            int(board.game_type),
                        ),
                    )
                    for slot in board.players
                ]
            )

        if board.game_over:
            board_lang = getattr(board, "lang", "fa") or "fa"
            play_again_text = self._translator.t(I18nKeys.PLAY_AGAIN_BUTTON, board_lang)
            rows.append(
                [
                    InlineKeyboardButton(
                        text=play_again_text,
                        switch_inline_query_current_chat="",
                    )
                ]
            )
        else:
            rows.append(
                [
                    InlineKeyboardButton(
                        text="🕹 Kio Games bot | ربات بازی کایو 🕹",
                        url=bot_url,
                    )
                ]
            )
        return InlineKeyboardMarkup(inline_keyboard=rows)

    def language_switcher(self) -> InlineKeyboardMarkup:
        rows: list[list[InlineKeyboardButton]] = []
        row: list[InlineKeyboardButton] = []
        for code, label in LANGUAGE_OPTIONS:
            row.append(
                InlineKeyboardButton(
                    text=label,
                    callback_data=CallbackService.build_change_lang(code),
                )
            )
            if len(row) == 2:
                rows.append(row)
                row = []
        if row:
            rows.append(row)
        return InlineKeyboardMarkup(inline_keyboard=rows)

    def make_game_button(self, lang: str, creator_id: int, game_type: GameTypeId) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text=self._translator.t(I18nKeys.CREATE_GAME_BUTTON, lang),
            callback_data=CallbackService.build_make_game(creator_id, int(game_type)),
        )
