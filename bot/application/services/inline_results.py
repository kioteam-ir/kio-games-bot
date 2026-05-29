from __future__ import annotations

from aiogram.types import InlineQueryResultArticle, InputTextMessageContent

from bot.application.dto.game import InlineGamesContext
from bot.domain.schemas.sponsor import SponsorRecord
from bot.domain.schemas.texts import CommandKey
from bot.infrastructure.i18n.texts import TextsService
from bot.infrastructure.telegram.keyboards import KeyboardService


class InlineQueryResultService:
    def __init__(self, texts: TextsService, keyboards: KeyboardService) -> None:
        self._texts = texts
        self._keyboards = keyboards

    def build_results(
        self,
        context: InlineGamesContext,
        user_id: int,
        sponsors: list[SponsorRecord],
    ) -> list[InlineQueryResultArticle]:
        if context.is_banned:
            lang = context.lang
            return [
                InlineQueryResultArticle(
                    id="-1",
                    title=self._texts.get(lang, CommandKey.YOU_ARE_BANNED_TITLE),
                    input_message_content=InputTextMessageContent(
                        message_text=self._texts.get(lang, CommandKey.YOU_ARE_BANNED_TEXT),
                    ),
                    description=self._texts.get(lang, CommandKey.YOU_ARE_BANNED_TEXT),
                )
            ]

        lang = context.lang
        results: list[InlineQueryResultArticle] = [
            InlineQueryResultArticle(
                id="999",
                title=self._texts.get(lang, CommandKey.CHANGE_YOUR_LANG),
                input_message_content=InputTextMessageContent(
                    message_text=self._texts.get(lang, CommandKey.CHANGE_YOUR_LANG_TEXT),
                ),
                description=self._texts.get(lang, CommandKey.CHANGE_YOUR_LANG_TEXT),
                reply_markup=self._keyboards.language_switcher(),
            )
        ]
        for game in context.games:
            description = (
                f"{game.description}\n\n{self._texts.get(lang, CommandKey.CREATE_GAME_TEXT)}"
            )
            results.append(
                InlineQueryResultArticle(
                    id=str(int(game.game_type_id)),
                    title=game.title,
                    input_message_content=InputTextMessageContent(message_text=description),
                    description=game.description,
                    thumbnail_url=game.thumb_url,
                    reply_markup=self._keyboards.sponsor_keyboard(
                        sponsors,
                        extra_row=[
                            self._keyboards.make_game_button(lang, user_id, game.game_type_id)
                        ],
                    ),
                )
            )
        return results
