from __future__ import annotations

from aiogram import Router
from aiogram.types import CallbackQuery, ChosenInlineResult, InlineQuery, Message

from bot.application.dto.game import (
    JoinGameRequest,
    MakeGameRequest,
    MoveGameRequest,
    ResolvedUserContext,
    UseCaseError,
)
from bot.application.services.game_flow import GameFlowService
from bot.application.services.inline_results import InlineQueryResultService
from bot.application.services.session_manager import GameSessionManager
from bot.config.session import SessionConfigClass
from bot.core.container import AppContainer
from bot.domain.repositories import telegram_player_from_user
from bot.domain.schemas.game import GameTypeId
from bot.infrastructure.callback.payloads import (
    CellMoveCallback,
    ChangeLangCallback,
    JoinGameCallback,
    MakeGameCallback,
    PlayerInfoCallback,
)
from bot.infrastructure.i18n.translator import Translator
from bot.infrastructure.telegram.callbacks import answer_callback
from bot.infrastructure.telegram.editing import edit_callback_message
from bot.infrastructure.telegram.keyboards import KeyboardService
from bot.locales.i18n_keys import I18nKeys
from bot.presentation.filters.callback_data import MakeGameCallbackFilter
from bot.presentation.filters.game import GameSessionFilter
from bot.presentation.filters.sponsor import SponsorOkFilter, SponsorRequiredFilter
from bot.presentation.filters.user import BannedUserFilter, NotBannedFilter, ResolvedUserFilter

router = Router(name="inline")


@router.inline_query(ResolvedUserFilter())
async def inline_games_handler(
    inline_query: InlineQuery,
    inline_results: InlineQueryResultService,
    session_config: SessionConfigClass,
    container: AppContainer,
    user_context: ResolvedUserContext,
) -> None:
    from bot.application.dto.game import InlineGamesContext

    if inline_query.from_user is None:
        await inline_query.answer([], cache_time=1, is_personal=True)
        return
    context = InlineGamesContext(
        user=user_context.user,
        lang=user_context.lang,
        games=container.catalog.list_for_lang(user_context.lang),
        is_banned=user_context.user.is_banned,
    )
    sponsors = await container.sponsor_repo.list_active()
    results = inline_results.build_results(context, inline_query.from_user.id, sponsors)
    await inline_query.answer(
        results,  # type: ignore[arg-type]
        cache_time=session_config.inline_query_cache_time,
        is_personal=True,
    )


@router.callback_query(ChangeLangCallback.filter())
async def change_lang_handler(
    callback: CallbackQuery,
    callback_data: ChangeLangCallback,
    change_language_service: object,
) -> None:
    from bot.application.services.game_flow import ChangeLanguageService

    if callback.from_user is None or not isinstance(change_language_service, ChangeLanguageService):
        await answer_callback(callback)
        return
    result = await change_language_service.change(callback.from_user.id, callback_data.lang)
    await edit_callback_message(callback, text=result.message_text)
    await callback.answer()


@router.callback_query(PlayerInfoCallback.filter(), ResolvedUserFilter())
async def player_info_handler(
    callback: CallbackQuery,
    callback_data: PlayerInfoCallback,
    player_stats_service: object,
    user_context: ResolvedUserContext,
) -> None:
    from bot.application.services.game_flow import PlayerStatsService

    if not isinstance(player_stats_service, PlayerStatsService):
        await answer_callback(callback)
        return
    result = await player_stats_service.stats(
        callback_data.player_id,
        callback_data.game_type,
        user_context.lang,
    )
    await callback.answer(result.text, show_alert=True)


@router.chosen_inline_result()
async def chosen_inline_result_handler(chosen: ChosenInlineResult) -> None:
    _ = chosen


@router.callback_query(
    MakeGameCallbackFilter(),
    ResolvedUserFilter(),
)
async def make_game_handler(
    callback: CallbackQuery,
    callback_data: MakeGameCallback,
    game_flow_service: GameFlowService,
    keyboards: KeyboardService,
    translator: Translator,
    user_context: ResolvedUserContext,
    container: AppContainer,
) -> None:
    lang = user_context.lang
    if callback.from_user is None or callback.inline_message_id is None or callback.bot is None:
        await answer_callback(callback)
        return
    if callback.from_user.id != callback_data.creator_id:
        await answer_callback(
            callback,
            translator.t(I18nKeys.NOT_YOUR_GAME, lang),
            show_alert=True,
        )
        return
    if user_context.user.is_banned:
        await answer_callback(
            callback,
            translator.t(I18nKeys.YOU_ARE_BANNED_TEXT, lang),
            show_alert=True,
        )
        return
    if container.sponsor_checker is None or not await container.sponsor_checker.is_member_of_all(
        callback.from_user.id,
    ):
        await answer_callback(
            callback,
            translator.t(I18nKeys.JOIN_FIRST, lang),
            show_alert=True,
        )
        return

    if callback_data.game_type is GameTypeId.MINE and callback_data.mine_count == 0:
        await callback.bot.edit_message_text(
            inline_message_id=callback.inline_message_id,
            text=translator.t(I18nKeys.CHOOSE_NUMBER_OF_MINES, user_context.lang),
            reply_markup=keyboards.mine_count_picker(user_context.lang, callback_data.creator_id),
        )
        await callback.answer()
        return

    request = MakeGameRequest(
        creator=telegram_player_from_user(callback.from_user),
        game_type=callback_data.game_type,
        inline_message_id=callback.inline_message_id,
        lang=user_context.lang,
        mine_count=callback_data.mine_count,
    )
    result = await game_flow_service.create(request)
    if isinstance(result, UseCaseError):
        await callback.answer(
            translator.t(result.message_key, user_context.lang),
            show_alert=result.alert,
        )
        return
    await callback.bot.edit_message_text(
        inline_message_id=callback.inline_message_id,
        text=result.text,
        reply_markup=keyboards.waiting_keyboard(user_context.lang, result.game_id),
    )
    await callback.answer()


@router.callback_query(
    JoinGameCallback.filter(),
    ResolvedUserFilter(),
    NotBannedFilter(),
    SponsorOkFilter(),
    GameSessionFilter(),
)
async def join_game_handler(
    callback: CallbackQuery,
    callback_data: JoinGameCallback,
    game_flow_service: GameFlowService,
    keyboards: KeyboardService,
    translator: Translator,
    user_context: ResolvedUserContext,
    game_id: int,
) -> None:
    if callback.from_user is None or callback.inline_message_id is None or callback.bot is None:
        await answer_callback(callback)
        return
    request = JoinGameRequest(
        player=telegram_player_from_user(callback.from_user),
        game_id=game_id,
        lang=user_context.lang,
    )
    result = await game_flow_service.join(request)
    if isinstance(result, UseCaseError):
        await callback.answer(
            translator.t(result.message_key, user_context.lang),
            show_alert=result.alert,
        )
        return
    await callback.bot.edit_message_text(
        inline_message_id=callback.inline_message_id,
        text=result.view.text,
        reply_markup=keyboards.game_board(result.view),
    )
    await callback.answer()


@router.callback_query(
    CellMoveCallback.filter(),
    ResolvedUserFilter(),
    GameSessionFilter(),
)
async def cell_move_handler(
    callback: CallbackQuery,
    callback_data: CellMoveCallback,
    game_flow_service: GameFlowService,
    session_manager: GameSessionManager,
    keyboards: KeyboardService,
    translator: Translator,
    user_context: ResolvedUserContext,
    game_id: int,
    game_session: object | None = None,
) -> None:
    from bot.domain.entities.game_session import GameSession

    if callback.from_user is None or callback.inline_message_id is None or callback.bot is None:
        await answer_callback(callback)
        return
    prefetched = game_session if isinstance(game_session, GameSession) else None
    request = MoveGameRequest(
        player_id=callback.from_user.id,
        game_id=game_id,
        row=callback_data.row,
        col=callback_data.col,
        lang=user_context.lang,
    )
    result = await game_flow_service.move(request, session=prefetched)
    if isinstance(result, UseCaseError):
        await callback.answer(
            translator.t(result.message_key, user_context.lang),
            show_alert=result.alert,
        )
        return
    await callback.bot.edit_message_text(
        inline_message_id=callback.inline_message_id,
        text=result.view.text,
        reply_markup=keyboards.game_board(result.view),
    )
    if result.should_delete_session:
        await session_manager.delete(game_id)
    await callback.answer()


@router.message(ResolvedUserFilter(), BannedUserFilter())
async def banned_message_handler(
    message: Message,
    banned_context: ResolvedUserContext,
    translator: Translator,
) -> None:
    await message.answer(translator.t(I18nKeys.YOU_ARE_BANNED_TEXT, banned_context.lang))


@router.message(ResolvedUserFilter(), NotBannedFilter(), SponsorRequiredFilter())
async def sponsor_gate_handler(
    message: Message,
    sponsor_required: bool | None = None,
    join_message: str | None = None,
    sponsors: list[object] | None = None,
    keyboards: KeyboardService | None = None,
) -> None:
    if not sponsor_required or keyboards is None or join_message is None:
        return
    from bot.domain.schemas.sponsor import SponsorRecord

    sponsor_rows = [s for s in (sponsors or []) if isinstance(s, SponsorRecord)]
    await message.answer(
        join_message,
        reply_markup=keyboards.sponsor_keyboard(sponsor_rows),
    )