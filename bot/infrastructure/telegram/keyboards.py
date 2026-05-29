# ruff: noqa: E501
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.application.dto.game import GameBoardView
from bot.domain.entities.game_session import GameSession
from bot.domain.games.connect.with_friend import VsFriendEngine
from bot.domain.schemas.game import GameTypeId
from bot.domain.schemas.sponsor import SponsorRecord
from bot.infrastructure.callback.service import CallbackService
from bot.infrastructure.i18n.translator import Translator
from bot.locales.i18n_keys import I18nKeys

_NUMBER_EMOJI: dict[int, str] = {
    0: "0️⃣",
    1: "1️⃣",
    2: "2️⃣",
    3: "3️⃣",
    4: "4️⃣",
    5: "5️⃣",
    6: "6️⃣",
    7: "7️⃣",
    8: "8️⃣",
    9: "9️⃣",
    10: "🔟",
}


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
        rows = [
            [InlineKeyboardButton(text=f"🎫 {s.name.strip()} 🎫", url=str(s.link))]
            for s in sponsors
        ]
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
        return self._build_board(view.session, view.game_id, view.game_over)

    def _build_board(self, session: GameSession, game_id: int, game_over: bool) -> InlineKeyboardMarkup:
        rows: list[list[InlineKeyboardButton]] = []
        active = not game_over
        bot_url = f"https://t.me/{self._bot_username}"
        row_idx = 1
        for row in session.game_engine.board:
            buttons: list[InlineKeyboardButton] = []
            col_idx = 1
            for cell in row:
                label = str(cell.as_symbol if session.is_xo else cell.as_color)
                buttons.append(
                    InlineKeyboardButton(
                        text=label,
                        callback_data=CallbackService.build_cell_move(row_idx, col_idx, game_id)
                        if active
                        else None,
                        url=None if active else bot_url,
                    )
                )
                col_idx += 1
            rows.append(buttons)
            row_idx += 1

        if isinstance(session.game_engine, VsFriendEngine):
            legal = session.game_engine.legal_moves()
            move_row: list[InlineKeyboardButton] = []
            for col in range(session.game_engine.cols):
                label = "🚫" if col not in legal else _NUMBER_EMOJI[col + 1]
                move_row.append(
                    InlineKeyboardButton(
                        text=label,
                        callback_data=CallbackService.build_cell_move(0, col + 1, game_id)
                        if active
                        else None,
                        url=None if active else bot_url,
                    )
                )
            rows.append(move_row)

        if len(session.players) == 2:
            current_is_p1 = session.current_player.id == session.players[0].id
            rows.append(
                [
                    InlineKeyboardButton(
                        text=f"🎮 {'🔺' if current_is_p1 else ''} {session.players[0].first_name}",
                        callback_data=CallbackService.build_player_info(
                            session.players[0].id,
                            int(session.game_type),
                        ),
                    ),
                    InlineKeyboardButton(
                        text=f"🎮 {'' if current_is_p1 else '🔺'} {session.players[1].first_name}",
                        callback_data=CallbackService.build_player_info(
                            session.players[1].id,
                            int(session.game_type),
                        ),
                    ),
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
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🇹🇷 Türkçe 🇹🇷", callback_data=CallbackService.build_change_lang("tr"))],
                [InlineKeyboardButton(text="🇺🇸 English 🇺🇸", callback_data=CallbackService.build_change_lang("en"))],
                [InlineKeyboardButton(text="🇮🇷 فارسی 🇮🇷", callback_data=CallbackService.build_change_lang("fa"))],
            ]
        )

    def make_game_button(self, lang: str, creator_id: int, game_type: GameTypeId) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text=self._translator.t(I18nKeys.CREATE_GAME_BUTTON, lang),
            callback_data=CallbackService.build_make_game(creator_id, int(game_type)),
        )
