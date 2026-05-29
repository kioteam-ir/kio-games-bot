from abc import ABC, abstractmethod

from bot.domain.schemas.game import GameMatchSummary, GameTypeId, PlayerGameStats
from bot.domain.schemas.player import TelegramPlayer
from bot.domain.schemas.sponsor import SponsorRecord
from bot.domain.schemas.user import UserRecord


class UserRepository(ABC):
    @abstractmethod
    async def get_or_create(
        self,
        user_id: int,
        *,
        name: str = "",
        username: str = "",
        lang_code: str = "fa",
    ) -> UserRecord: ...

    @abstractmethod
    async def change_lang(self, user_id: int, lang_code: str) -> None: ...

    @abstractmethod
    async def get_game_stats(self, user_id: int, game_type: GameTypeId) -> PlayerGameStats: ...


class GameRepository(ABC):
    @abstractmethod
    async def record_match(
        self,
        player_1_id: int,
        player_2_id: int,
        result: str,
        game_type: GameTypeId,
        inline_message_id: str,
    ) -> GameMatchSummary: ...


class SponsorRepository(ABC):
    @abstractmethod
    async def list_active(self) -> list[SponsorRecord]: ...


class SponsorMembershipChecker(ABC):
    @abstractmethod
    async def is_member_of_all(self, user_id: int) -> bool: ...


def telegram_player_from_user(user: object) -> TelegramPlayer:
    from aiogram.types import User as AiogramUser

    if not isinstance(user, AiogramUser):
        msg = f"Expected aiogram User, got {type(user)!r}"
        raise TypeError(msg)
    return TelegramPlayer(
        id=user.id,
        first_name=user.first_name or "Player",
        username=user.username,
        lang_code=user.language_code,
    )
