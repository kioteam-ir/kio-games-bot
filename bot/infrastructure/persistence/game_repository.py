from __future__ import annotations

from asgiref.sync import sync_to_async

from bot.domain.repositories import GameRepository
from bot.domain.schemas.game import GameMatchSummary, GameTypeId, HeadToHeadStats
from bot.infrastructure.persistence.django_setup import setup_django


class DjangoGameRepository(GameRepository):
    def __init__(self) -> None:
        setup_django()

    async def record_match(
        self,
        player_1_id: int,
        player_2_id: int,
        result: str,
        game_type: GameTypeId,
        inline_message_id: str,
    ) -> GameMatchSummary:
        from app.models import Game

        raw = await sync_to_async(Game.geme_add)(
            player_1_id,
            player_2_id,
            int(game_type),
            result,
            inline_message_id,
        )
        head_to_head = HeadToHeadStats.model_validate(raw)
        return GameMatchSummary(head_to_head=head_to_head, result=result)
