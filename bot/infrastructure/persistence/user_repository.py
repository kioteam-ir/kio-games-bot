from __future__ import annotations

from asgiref.sync import sync_to_async

from bot.domain.repositories import UserRepository
from bot.domain.schemas.game import GameTypeId, PlayerGameStats
from bot.domain.schemas.user import UserRecord
from bot.infrastructure.persistence.django_setup import setup_django


class DjangoUserRepository(UserRepository):
    def __init__(self) -> None:
        setup_django()

    async def get_or_create(
        self,
        user_id: int,
        *,
        name: str = "",
        username: str = "",
        lang_code: str = "fa",
    ) -> UserRecord:
        from app.models import User

        raw = await sync_to_async(User.get_or_create)(
            user_id,
            name,
            username,
            False,
            False,
            lang_code,
        )
        return UserRecord.model_validate(raw)

    async def change_lang(self, user_id: int, lang_code: str) -> None:
        from app.models import User

        await sync_to_async(User.change_lang)(user_id, lang_code)

    async def get_game_stats(self, user_id: int, game_type: GameTypeId) -> PlayerGameStats:
        from app.models import User

        try:
            raw = await sync_to_async(User.retrieve_game)(user_id, int(game_type))
        except Exception:
            return PlayerGameStats()
        return PlayerGameStats(
            total=int(raw["total"]),
            wins=int(raw["wins"]),
            losses=int(raw["losses"]),
            draws=int(raw["draws"]),
        )
