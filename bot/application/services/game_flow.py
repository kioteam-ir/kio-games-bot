from __future__ import annotations

from bot.application.dto.game import (
    ChangeLangResult,
    CreateGameResult,
    GameBoardView,
    InlineGamesContext,
    JoinGameRequest,
    JoinGameResult,
    MakeGameRequest,
    MoveGameRequest,
    MoveGameResult,
    PlayerStatsResult,
    ResolvedUserContext,
    SessionTimeoutResult,
    UseCaseError,
)
from bot.application.services.board_state import BoardStateBuilder
from bot.application.services.game_catalog import GameCatalogService
from bot.application.services.session_manager import GameSessionManager
from bot.domain.entities.game_session import GameSession
from bot.domain.games.registry import create_engine, get_game_module
from bot.domain.repositories import GameRepository, UserRepository, telegram_player_from_user
from bot.domain.schemas.game import GameMatchSummary, GameResultKind, GameTypeId, PlayerGameStats
from bot.infrastructure.i18n.translator import Translator
from bot.locales.i18n_keys import I18nKeys


class UserService:
    def __init__(self, user_repo: UserRepository, translator: Translator) -> None:
        self._users = user_repo
        self._translator = translator

    async def resolve_user(
        self,
        tg_user: object,
        *,
        lang_hint: str | None = None,
    ) -> ResolvedUserContext:
        player = telegram_player_from_user(tg_user)
        lang = self._translator.resolve_lang(lang_hint or player.lang_code)
        user = await self._users.get_or_create(
            player.id,
            name=player.first_name,
            username=player.username or "",
            lang_code=lang,
        )
        return ResolvedUserContext(user=user, lang=user.lang_code)


class InlineGamesService:
    def __init__(
        self,
        user_service: UserService,
        catalog: GameCatalogService,
    ) -> None:
        self._users = user_service
        self._catalog = catalog

    async def build_context(self, tg_user: object, lang_hint: str | None) -> InlineGamesContext:
        resolved = await self._users.resolve_user(tg_user, lang_hint=lang_hint)
        return InlineGamesContext(
            user=resolved.user,
            lang=resolved.lang,
            games=self._catalog.list_for_lang(resolved.lang),
            is_banned=resolved.user.is_banned,
        )


class ChangeLanguageService:
    def __init__(self, user_repo: UserRepository, translator: Translator) -> None:
        self._users = user_repo
        self._translator = translator

    async def change(self, user_id: int, lang: str) -> ChangeLangResult:
        resolved_lang = self._translator.resolve_lang(lang)
        await self._users.change_lang(user_id, resolved_lang)
        return ChangeLangResult(
            alert_text=self._translator.t(I18nKeys.LANG_CHANGED, resolved_lang),
        )


class PlayerStatsService:
    def __init__(self, user_repo: UserRepository, translator: Translator) -> None:
        self._users = user_repo
        self._translator = translator

    async def stats(self, player_id: int, game_type: GameTypeId, lang: str) -> PlayerStatsResult:
        stats: PlayerGameStats = await self._users.get_game_stats(player_id, game_type)
        return PlayerStatsResult(
            text=self._translator.t(
                I18nKeys.PLAYER_GAME_STATS,
                lang,
                all_games=stats.total,
                wins=stats.wins,
                losses=stats.losses,
                draws=stats.draws,
            ),
        )


class GameFlowService:
    def __init__(
        self,
        sessions: GameSessionManager,
        catalog: GameCatalogService,
        game_repo: GameRepository,
        user_repo: UserRepository,
        translator: Translator,
    ) -> None:
        self._sessions = sessions
        self._catalog = catalog
        self._games = game_repo
        self._users = user_repo
        self._translator = translator

    async def create(self, request: MakeGameRequest) -> CreateGameResult | UseCaseError:
        entry = self._catalog.get(request.lang, request.game_type)
        engine = create_engine(entry)
        session = GameSession(
            game_engine=engine,
            inline_message_id=request.inline_message_id,
            current_player=request.creator,
            players=[request.creator],
            game_type=request.game_type,
            lang=request.lang,
        )
        game_id = await self._sessions.push(session)
        waiting = self._translator.t(I18nKeys.WAITING_FOR_PLAYER, request.lang)
        text = f"{waiting}\n{entry.description}"
        return CreateGameResult(text=text, game_id=game_id)

    async def join(self, request: JoinGameRequest) -> JoinGameResult | UseCaseError:
        session = await self._sessions.get(request.game_id)
        if session is None:
            return UseCaseError(message_key=I18nKeys.NOT_YOUR_GAME)
        if request.player.id in {p.id for p in session.players}:
            return UseCaseError(message_key=I18nKeys.CANNOT_PLAY_WITH_YOURSELF)
        await self._users.get_or_create(
            request.player.id,
            name=request.player.first_name,
            username=request.player.username or "",
            lang_code=self._translator.resolve_lang(request.player.lang_code),
        )
        session.players.append(request.player)
        await self._sessions.save(request.game_id, session)
        creator = await self._users.get_or_create(session.players[0].id)
        view = self._build_board_view(session, request.game_id, creator.lang_code, game_over=False)
        return JoinGameResult(view=view)

    async def move(self, request: MoveGameRequest) -> MoveGameResult | UseCaseError:
        session = await self._sessions.get(request.game_id)
        if session is None:
            return UseCaseError(message_key=I18nKeys.NOT_YOUR_GAME)
        if request.player_id not in {p.id for p in session.players}:
            return UseCaseError(message_key=I18nKeys.NOT_YOUR_GAME)
        if session.current_player.id != request.player_id:
            return UseCaseError(message_key=I18nKeys.NOT_YOUR_TURN)

        engine = session.game_engine
        module = get_game_module(session.game_type)
        if not module.apply_ui_move(engine, row=request.row, col=request.col):
            return UseCaseError(message_key=I18nKeys.COLUMN_FULL)

        new_player = (
            session.players[0]
            if session.current_player.id != session.players[0].id
            else session.players[1]
        )
        session.current_player = new_player
        await self._sessions.save(request.game_id, session)

        creator = await self._users.get_or_create(session.players[0].id)
        game_lang = creator.lang_code
        game_over = engine.ended or engine.is_draw()
        match_summary = None
        if game_over and len(session.players) == 2:
            result = (
                GameResultKind.DRAW.value
                if engine.is_draw()
                else f"player_{engine.winner.value if engine.winner else 1}"
            )
            match_summary = await self._games.record_match(
                session.players[0].id,
                session.players[1].id,
                result,
                session.game_type,
                session.inline_message_id,
            )
        view = self._build_board_view(
            session,
            request.game_id,
            game_lang,
            game_over=game_over,
            match_summary=match_summary,
        )
        return MoveGameResult(
            view=view,
            match_summary=match_summary,
            should_delete_session=game_over,
        )

    async def get_state(self, game_id: int) -> GameBoardView | UseCaseError:
        session = await self._sessions.get(game_id)
        if session is None:
            return UseCaseError(message_key=I18nKeys.NOT_YOUR_GAME)
        creator = await self._users.get_or_create(session.players[0].id)
        game_over = session.game_engine.ended or session.game_engine.is_draw()
        return self._build_board_view(session, game_id, creator.lang_code, game_over=game_over)

    async def handle_timeout(
        self,
        game_id: int,
        session: GameSession,
    ) -> SessionTimeoutResult | None:
        creator = await self._users.get_or_create(session.players[0].id)
        lang = creator.lang_code
        if len(session.players) == 2:
            if session.game_engine.ended:
                return None
            winner_index = 1 if session.current_player.id == session.players[0].id else 0
            winner_player = session.players[winner_index]
            result = f"player_{winner_index + 1}"
            summary = await self._games.record_match(
                session.players[0].id,
                session.players[1].id,
                result,
                session.game_type,
                session.inline_message_id,
            )
            ended = self._translator.t(
                I18nKeys.GAME_ENDED_TEXT,
                lang,
                winner=winner_player.first_name,
                total=summary.head_to_head.total,
                game=self._translator.t(I18nKeys.GAME, lang),
                p1_name=session.players[0].first_name,
                p1_wins=summary.head_to_head.p1_wins,
                p2_name=session.players[1].first_name,
                p2_wins=summary.head_to_head.p2_wins,
                draws=summary.head_to_head.draws,
            )
            stopped = self._translator.t(I18nKeys.GAME_STOPPED, lang)
            text = f"{stopped}\n\n{ended}"
            board = BoardStateBuilder.build(session, game_id, game_over=True)
            return SessionTimeoutResult(
                inline_message_id=session.inline_message_id,
                text=text,
                game_id=game_id,
                game_over=True,
                lang=lang,
                board=board,
            )
        text = self._translator.t(I18nKeys.PLAY_WITH_COOL_PEOPLE_TEXT, lang)
        return SessionTimeoutResult(
            inline_message_id=session.inline_message_id,
            text=text,
            game_id=game_id,
            game_over=True,
            lang=lang,
            board=None,
        )

    def _build_board_view(
        self,
        session: GameSession,
        game_id: int,
        lang: str,
        *,
        game_over: bool,
        match_summary: GameMatchSummary | None = None,
    ) -> GameBoardView:
        engine = session.game_engine
        if game_over and match_summary is not None:
            is_draw = engine.is_draw()
            winner_name = (
                self._translator.t(I18nKeys.GAME_IS_DRAW_TEXT, lang)
                if is_draw
                else session.players[engine.winner.value - 1].first_name  # type: ignore[union-attr]
            )
            text = self._translator.t(
                I18nKeys.GAME_ENDED_TEXT,
                lang,
                winner=winner_name,
                total=match_summary.head_to_head.total,
                game=self._translator.t(I18nKeys.GAME, lang),
                p1_name=session.players[0].first_name,
                p1_wins=match_summary.head_to_head.p1_wins,
                p2_name=session.players[1].first_name,
                p2_wins=match_summary.head_to_head.p2_wins,
                draws=match_summary.head_to_head.draws,
            )
        elif game_over:
            text = self._translator.t(I18nKeys.PLAY_WITH_COOL_PEOPLE_TEXT, lang)
        else:
            text = self._translator.t(
                I18nKeys.GAME_IN_PROGRESS_TEXT,
                lang,
                name=session.current_player.first_name,
                color=engine.current_player.as_color,
            )
        board = BoardStateBuilder.build(session, game_id, game_over=game_over)
        return GameBoardView(text=text, game_id=game_id, game_over=game_over, board=board)
