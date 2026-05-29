from __future__ import annotations

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.infrastructure.database.connection import get_session_factory, session_scope
from api.infrastructure.database.models import AppGame, AppScore
from bot.domain.repositories import GameRepository
from bot.domain.schemas.game import GameMatchSummary, GameTypeId, HeadToHeadStats


async def _get_or_create_score(
    session: AsyncSession,
    user_id: int,
    game_type: int,
) -> AppScore:
    result = await session.execute(
        select(AppScore).where(
            AppScore.user_id == user_id,
            AppScore.game_type == game_type,
        )
    )
    score = result.scalar_one_or_none()
    if score is None:
        score = AppScore(user_id=user_id, game_type=game_type)
        session.add(score)
        await session.flush()
    return score


async def _apply_winner(session: AsyncSession, user_id: int, game_type: int) -> None:
    score = await _get_or_create_score(session, user_id, game_type)
    score.games += 1
    score.wins += 1


async def _apply_loser(session: AsyncSession, user_id: int, game_type: int) -> None:
    score = await _get_or_create_score(session, user_id, game_type)
    score.games += 1
    score.losses += 1


async def _apply_draw(session: AsyncSession, user_id: int, game_type: int) -> None:
    score = await _get_or_create_score(session, user_id, game_type)
    score.games += 1


async def _update_scores(
    session: AsyncSession,
    player_1_id: int,
    player_2_id: int,
    result: str,
    game_type: int,
) -> None:
    if result == "player_2":
        await _apply_loser(session, player_1_id, game_type)
        await _apply_winner(session, player_2_id, game_type)
    elif result == "player_1":
        await _apply_winner(session, player_1_id, game_type)
        await _apply_loser(session, player_2_id, game_type)
    else:
        await _apply_draw(session, player_1_id, game_type)
        await _apply_draw(session, player_2_id, game_type)


async def _shared_game(
    session: AsyncSession,
    game: AppGame,
) -> HeadToHeadStats:
    player_1_id = game.player_1_id
    player_2_id = game.player_2_id
    if player_1_id is None or player_2_id is None:
        return HeadToHeadStats(total=0, p1_wins=0, p2_wins=0, draws=0)

    pair_filter = and_(
        AppGame.type == game.type,
        or_(
            and_(AppGame.player_1_id == player_1_id, AppGame.player_2_id == player_2_id),
            and_(AppGame.player_1_id == player_2_id, AppGame.player_2_id == player_1_id),
        ),
    )

    total = await session.scalar(select(func.count()).select_from(AppGame).where(pair_filter))

    p1_win_filter = and_(
        pair_filter,
        or_(
            and_(AppGame.player_1_id == player_1_id, AppGame.result == "player_1"),
            and_(AppGame.player_2_id == player_1_id, AppGame.result == "player_2"),
        ),
    )
    p1_wins = await session.scalar(select(func.count()).select_from(AppGame).where(p1_win_filter))

    p2_win_filter = and_(
        pair_filter,
        or_(
            and_(AppGame.player_1_id == player_2_id, AppGame.result == "player_1"),
            and_(AppGame.player_2_id == player_2_id, AppGame.result == "player_2"),
        ),
    )
    p2_wins = await session.scalar(select(func.count()).select_from(AppGame).where(p2_win_filter))

    draw_filter = and_(pair_filter, AppGame.result == "draw")
    draws = await session.scalar(select(func.count()).select_from(AppGame).where(draw_filter))

    return HeadToHeadStats(
        total=int(total or 0),
        p1_wins=int(p1_wins or 0),
        p2_wins=int(p2_wins or 0),
        draws=int(draws or 0),
    )


class SqlAlchemyGameRepository(GameRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession] | None = None) -> None:
        self._session_factory = session_factory or get_session_factory()

    async def record_match(
        self,
        player_1_id: int,
        player_2_id: int,
        result: str,
        game_type: GameTypeId,
        inline_message_id: str,
    ) -> GameMatchSummary:
        async with session_scope() as session:
            game = AppGame(
                player_1_id=player_1_id,
                player_2_id=player_2_id,
                type=int(game_type),
                result=result,
                mid=inline_message_id,
            )
            session.add(game)
            await session.flush()

            await _update_scores(session, player_1_id, player_2_id, result, int(game_type))
            head_to_head = await _shared_game(session, game)

        return GameMatchSummary(head_to_head=head_to_head, result=result)
