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
from bot.application.services.game_catalog import GameCatalogService
from bot.application.services.session_manager import GameSessionManager
from bot.domain.entities.game_session import GameSession
from bot.domain.games.connect.with_friend import VsFriendEngine
from bot.domain.games.XO.with_friend import VsFriendXO
from bot.domain.repositories import GameRepository, UserRepository, telegram_player_from_user
from bot.domain.schemas.game import GameResultKind, GameTypeId, PlayerGameStats
from bot.domain.schemas.texts import CommandKey
from bot.infrastructure.i18n.texts import TextsService


class UserService:
    def __init__(self, user_repo: UserRepository, texts: TextsService) -> None:
        self._users = user_repo
        self._texts = texts

    async def resolve_user(self, tg_user: object, *, lang_hint: str | None = None) -> ResolvedUserContext:
        player = telegram_player_from_user(tg_user)
        lang = self._texts.resolve_lang(lang_hint or player.lang_code)
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
    def __init__(self, user_repo: UserRepository, texts: TextsService) -> None:
        self._users = user_repo
        self._texts = texts

    async def change(self, user_id: int, lang: str) -> ChangeLangResult:
        resolved_lang = self._texts.resolve_lang(lang)
        await self._users.change_lang(user_id, resolved_lang)
        return ChangeLangResult(alert_text=self._texts.get(resolved_lang, CommandKey.LANG_CHANGED))


class PlayerStatsService:
    def __init__(self, user_repo: UserRepository, texts: TextsService) -> None:
        self._users = user_repo
        self._texts = texts

    async def stats(self, player_id: int, game_type: GameTypeId, lang: str) -> PlayerStatsResult:
        stats: PlayerGameStats = await self._users.get_game_stats(player_id, game_type)
        template = self._texts.get(lang, CommandKey.PLAYER_GAME_STATS)
        return PlayerStatsResult(
            text=template.format(
                all_games=stats.total,
                wins=stats.wins,
                losses=stats.losses,
                draws=stats.draws,
            )
        )


class GameFlowService:
    def __init__(
        self,
        sessions: GameSessionManager,
        catalog: GameCatalogService,
        game_repo: GameRepository,
        user_repo: UserRepository,
        texts: TextsService,
    ) -> None:
        self._sessions = sessions
        self._catalog = catalog
        self._games = game_repo
        self._users = user_repo
        self._texts = texts

    def _create_engine(self, entry: object, is_xo: bool) -> VsFriendXO | VsFriendEngine:
        from bot.domain.schemas.game import GameCatalogEntry

        if not isinstance(entry, GameCatalogEntry):
            msg = "Expected GameCatalogEntry"
            raise TypeError(msg)
        if is_xo:
            return VsFriendXO(entry.rows, entry.connect)
        return VsFriendEngine(entry.rows, entry.cols, entry.connect)

    async def create(self, request: MakeGameRequest) -> CreateGameResult | UseCaseError:
        entry = self._catalog.get(request.lang, request.game_type)
        engine = self._create_engine(entry, entry.is_xo)
        session = GameSession(
            game_engine=engine,
            inline_message_id=request.inline_message_id,
            current_player=request.creator,
            players=[request.creator],
            is_xo=entry.is_xo,
            game_type=request.game_type,
        )
        game_id = self._sessions.push(session)
        text = (
            f"{self._texts.get(request.lang, CommandKey.WAITING_FOR_PLAYER)}\n{entry.description}"
        )
        return CreateGameResult(text=text, game_id=game_id, session=session)

    async def join(self, request: JoinGameRequest) -> JoinGameResult | UseCaseError:
        session = self._sessions.get(request.game_id)
        if session is None:
            return UseCaseError(message_key=CommandKey.NOT_YOUR_GAME)
        if request.player.id in {p.id for p in session.players}:
            return UseCaseError(message_key=CommandKey.CANNOT_PLAY_WITH_YOURSELF)
        await self._users.get_or_create(
            request.player.id,
            name=request.player.first_name,
            username=request.player.username or "",
            lang_code=self._texts.resolve_lang(request.player.lang_code),
        )
        session.players.append(request.player)
        creator = await self._users.get_or_create(session.players[0].id)
        game_lang = creator.lang_code
        view = self._build_board_view(session, request.game_id, game_lang, game_over=False)
        return JoinGameResult(view=view)

    async def move(self, request: MoveGameRequest) -> MoveGameResult | UseCaseError:
        session = self._sessions.get(request.game_id)
        if session is None:
            return UseCaseError(message_key=CommandKey.NOT_YOUR_GAME)
        if request.player_id not in {p.id for p in session.players}:
            return UseCaseError(message_key=CommandKey.NOT_YOUR_GAME)
        if session.current_player.id != request.player_id:
            return UseCaseError(message_key=CommandKey.NOT_YOUR_TURN)

        row = request.row - 1
        col = request.col - 1
        engine = session.game_engine
        if session.is_xo:
            if not isinstance(engine, VsFriendXO):
                return UseCaseError(message_key=CommandKey.COLUMN_FULL)
            if not engine.is_valid_move((row, col)):
                return UseCaseError(message_key=CommandKey.COLUMN_FULL)
            engine.make_move((row, col))
        else:
            if not engine.is_column_playable(col):
                return UseCaseError(message_key=CommandKey.COLUMN_FULL)
            engine.make_move(col)

        new_player = (
            session.players[0]
            if session.current_player.id != session.players[0].id
            else session.players[1]
        )
        session.current_player = new_player

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

    async def handle_timeout(self, game_id: int, session: GameSession) -> SessionTimeoutResult | None:
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
            ended = self._texts.get(lang, CommandKey.GAME_ENDED_TEXT).format(
                winner=winner_player.first_name,
                total=summary.head_to_head.total,
                game=self._texts.get(lang, CommandKey.GAME),
                p1_name=session.players[0].first_name,
                p1_wins=summary.head_to_head.p1_wins,
                p2_name=session.players[1].first_name,
                p2_wins=summary.head_to_head.p2_wins,
                draws=summary.head_to_head.draws,
            )
            text = f"{self._texts.get(lang, CommandKey.GAME_STOPPED)}\n\n{ended}"
            return SessionTimeoutResult(
                inline_message_id=session.inline_message_id,
                text=text,
                game_id=game_id,
                game_over=True,
                session=session,
            )
        text = self._texts.get(lang, CommandKey.PLAY_WITH_COOL_PEOPLE_TEXT)
        return SessionTimeoutResult(
            inline_message_id=session.inline_message_id,
            text=text,
            game_id=game_id,
            game_over=True,
            session=session,
        )

    def _build_board_view(
        self,
        session: GameSession,
        game_id: int,
        lang: str,
        *,
        game_over: bool,
        match_summary: object | None = None,
    ) -> GameBoardView:
        engine = session.game_engine
        if game_over and match_summary is not None:
            from bot.domain.schemas.game import GameMatchSummary

            if not isinstance(match_summary, GameMatchSummary):
                msg = "Expected GameMatchSummary"
                raise TypeError(msg)
            is_draw = engine.is_draw()
            winner_name = (
                self._texts.get(lang, CommandKey.GAME_IS_DRAW_TEXT)
                if is_draw
                else session.players[engine.winner.value - 1].first_name  # type: ignore[union-attr]
            )
            text = self._texts.get(lang, CommandKey.GAME_ENDED_TEXT).format(
                winner=winner_name,
                total=match_summary.head_to_head.total,
                game=self._texts.get(lang, CommandKey.GAME),
                p1_name=session.players[0].first_name,
                p1_wins=match_summary.head_to_head.p1_wins,
                p2_name=session.players[1].first_name,
                p2_wins=match_summary.head_to_head.p2_wins,
                draws=match_summary.head_to_head.draws,
            )
        elif game_over:
            text = self._texts.get(lang, CommandKey.PLAY_WITH_COOL_PEOPLE_TEXT)
        else:
            text = self._texts.get(lang, CommandKey.GAME_IN_PROGRESS_TEXT).format(
                name=session.current_player.first_name,
                color=engine.current_player.as_color,
            )
        return GameBoardView(text=text, game_id=game_id, game_over=game_over, session=session)
