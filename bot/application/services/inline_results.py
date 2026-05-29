from __future__ import annotations

from aiogram.types import InlineQueryResultArticle, InputTextMessageContent

from bot.application.dto.game import InlineGamesContext
from bot.domain.schemas.sponsor import SponsorRecord
from bot.infrastructure.i18n.translator import Translator
from bot.infrastructure.telegram.keyboards import KeyboardService
from bot.locales.i18n_keys import I18nKeys


class InlineQueryResultService:
    def __init__(self, translator: Translator, keyboards: KeyboardService) -> None:
        self._translator = translator
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
                    title=self._translator.t(I18nKeys.YOU_ARE_BANNED_TITLE, lang),
                    input_message_content=InputTextMessageContent(
                        message_text=self._translator.t(I18nKeys.YOU_ARE_BANNED_TEXT, lang),
                    ),
                    description=self._translator.t(I18nKeys.YOU_ARE_BANNED_TEXT, lang),
                )
            ]

        lang = context.lang
        results: list[InlineQueryResultArticle] = [
            InlineQueryResultArticle(
                id="999",
                title=self._translator.t(I18nKeys.CHANGE_YOUR_LANG, lang),
                input_message_content=InputTextMessageContent(
                    message_text=self._translator.t(I18nKeys.CHANGE_YOUR_LANG_TEXT, lang),
                ),
                description=self._translator.t(I18nKeys.CHANGE_YOUR_LANG_TEXT, lang),
                reply_markup=self._keyboards.language_switcher(),
            )
        ]
        for game in context.games:
            description = f"{game.description}\n\n{self._translator.t(I18nKeys.CREATE_GAME_TEXT, lang)}"
            results.append(
                InlineQueryResultArticle(
                    id=str(int(game.game_type_id)),
                    title=game.title,
                    input_message_content=InputTextMessageContent(message_text=description),
                    description=game.description,
                    thumbnail_url=game.thumb_url,
                    reply_markup=self._keyboards.sponsor_keyboard(
                        sponsors,
                        extra_row=[self._keyboards.make_game_button(lang, user_id, game.game_type_id)],
                    ),
                )
            )
        return results
