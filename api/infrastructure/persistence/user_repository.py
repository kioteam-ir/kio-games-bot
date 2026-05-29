from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.infrastructure.database.connection import get_session_factory, session_scope
from api.infrastructure.database.models import AppScore, AppUser
from bot.domain.repositories import UserRepository
from bot.domain.schemas.game import GameTypeId, PlayerGameStats
from bot.domain.schemas.user import UserRecord


def _user_to_legacy_dict(user: AppUser) -> dict[str, object]:
    return {
        "id": user.id,
        "is_banned": user.is_banned,
        "is_superuser": user.is_superuser,
        "joined_time": user.joined_time,
        "lang_code": user.lang_code,
    }


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession] | None = None) -> None:
        self._session_factory = session_factory or get_session_factory()

    async def get_or_create(
        self,
        user_id: int,
        *,
        name: str = "",
        username: str = "",
        lang_code: str = "fa",
    ) -> UserRecord:
        async with session_scope() as session:
            user = await session.get(AppUser, user_id)
            if user is None:
                user = AppUser(
                    id=user_id,
                    name=name,
                    username=username,
                    lang_code=lang_code,
                    joined_time=datetime.now(tz=UTC).replace(tzinfo=None),
                )
                session.add(user)
                await session.flush()
            return UserRecord.model_validate(_user_to_legacy_dict(user))

    async def change_lang(self, user_id: int, lang_code: str) -> None:
        async with session_scope() as session:
            user = await session.get(AppUser, user_id)
            if user is None:
                msg = f"User {user_id} not found"
                raise LookupError(msg)
            user.lang_code = lang_code

    async def get_game_stats(self, user_id: int, game_type: GameTypeId) -> PlayerGameStats:
        async with self._session_factory() as session:
            result = await session.execute(
                select(AppScore).where(
                    AppScore.user_id == user_id,
                    AppScore.game_type == int(game_type),
                )
            )
            score = result.scalar_one_or_none()
            if score is None:
                return PlayerGameStats()
            return PlayerGameStats(
                total=score.games,
                wins=score.wins,
                losses=score.losses,
                draws=score.games - (score.wins + score.losses),
            )
