from __future__ import annotations

import pytest

from bot.application.dto.game import JoinGameRequest, MakeGameRequest, MoveGameRequest
from bot.application.services.game_catalog import GameCatalogService
from bot.application.services.game_flow import GameFlowService
from bot.application.services.session_manager import GameSessionManager, InMemoryGameSessionStorage
from bot.domain.repositories import GameRepository, UserRepository
from bot.domain.schemas.game import GameMatchSummary, GameTypeId, HeadToHeadStats, PlayerGameStats
from bot.domain.schemas.player import TelegramPlayer
from bot.domain.schemas.user import UserRecord
from bot.infrastructure.i18n.translator import Translator
from bot.locales.i18n_keys import I18nKeys


class FakeUserRepo(UserRepository):
    def __init__(self, lang: str = "en") -> None:
        self._lang = lang

    async def get_or_create(
        self,
        user_id: int,
        *,
        name: str = "",
        username: str = "",
        lang_code: str = "fa",
    ) -> UserRecord:
        from datetime import UTC, datetime

        return UserRecord(
            id=user_id,
            is_banned=False,
            is_superuser=False,
            lang_code=self._lang or lang_code,
            joined_time=datetime.now(tz=UTC),
            username=username,
            name=name,
        )

    async def change_lang(self, user_id: int, lang_code: str) -> None:
        self._lang = lang_code

    async def get_game_stats(self, user_id: int, game_type: GameTypeId) -> PlayerGameStats:
        return PlayerGameStats()


class FakeGameRepo(GameRepository):
    async def record_match(
        self,
        player_1_id: int,
        player_2_id: int,
        result: str,
        game_type: GameTypeId,
        inline_message_id: str,
    ) -> GameMatchSummary:
        return GameMatchSummary(
            head_to_head=HeadToHeadStats(total=1, p1_wins=1, p2_wins=0, draws=0),
            result=result,
        )


def _flow(translator: Translator) -> GameFlowService:
    sessions = GameSessionManager(InMemoryGameSessionStorage(), timeout=3600.0)
    return GameFlowService(
        sessions=sessions,
        catalog=GameCatalogService(),
        game_repo=FakeGameRepo(),
        user_repo=FakeUserRepo(lang="en"),
        translator=translator,
    )


@pytest.mark.asyncio
async def test_create_waiting_message(translator: Translator) -> None:
    flow = _flow(translator)
    creator = TelegramPlayer(id=1, first_name="Alice")
    result = await flow.create(
        MakeGameRequest(
            creator=creator,
            game_type=GameTypeId.CONNECT_4,
            inline_message_id="inline-1",
            lang="en",
        )
    )
    assert result.game_id > 0
    assert "Waiting" in result.text


@pytest.mark.asyncio
async def test_join_adds_second_player(translator: Translator) -> None:
    flow = _flow(translator)
    creator = TelegramPlayer(id=1, first_name="Alice")
    created = await flow.create(
        MakeGameRequest(
            creator=creator,
            game_type=GameTypeId.CONNECT_4,
            inline_message_id="inline-1",
            lang="en",
        )
    )
    joined = await flow.join(
        JoinGameRequest(
            player=TelegramPlayer(id=2, first_name="Bob"),
            game_id=created.game_id,
            lang="en",
        )
    )
    assert len(joined.view.board.players) == 2


@pytest.mark.asyncio
async def test_move_rejects_wrong_turn(translator: Translator) -> None:
    flow = _flow(translator)
    created = await flow.create(
        MakeGameRequest(
            creator=TelegramPlayer(id=1, first_name="Alice"),
            game_type=GameTypeId.CONNECT_4,
            inline_message_id="inline-1",
            lang="en",
        )
    )
    await flow.join(
        JoinGameRequest(
            player=TelegramPlayer(id=2, first_name="Bob"),
            game_id=created.game_id,
            lang="en",
        )
    )
    err = await flow.move(MoveGameRequest(game_id=created.game_id, player_id=2, row=1, col=1, lang="en"))
    assert err.message_key == I18nKeys.NOT_YOUR_TURN


@pytest.mark.asyncio
async def test_connect_move_updates_board(translator: Translator) -> None:
    flow = _flow(translator)
    created = await flow.create(
        MakeGameRequest(
            creator=TelegramPlayer(id=1, first_name="Alice"),
            game_type=GameTypeId.CONNECT_4,
            inline_message_id="inline-1",
            lang="en",
        )
    )
    await flow.join(
        JoinGameRequest(
            player=TelegramPlayer(id=2, first_name="Bob"),
            game_id=created.game_id,
            lang="en",
        )
    )
    moved = await flow.move(MoveGameRequest(game_id=created.game_id, player_id=1, row=0, col=1, lang="en"))
    assert moved.view.board.game_id == created.game_id
    session = await flow._sessions.get(created.game_id)
    assert session is not None
    assert session.game_engine.move_count == 1
