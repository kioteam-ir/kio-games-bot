# ruff: noqa: E501
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

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

    def waiting_keyboard(self, lang: str, game_id: int) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=self._translator.t(I18nKeys.IPLAY, lang),
                        callback_data=CallbackService.build_join_game(game_id),
                    )
                ]
            ]
        )

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
