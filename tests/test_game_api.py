from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import bot.i18n_bootstrap  # noqa: F401
from api.presentation.routes.games import router as games_router
from bot.core.container import AppContainer
from bot.domain.repositories import SponsorRepository
from bot.domain.schemas.game import GameTypeId
from bot.domain.schemas.sponsor import SponsorRecord
from tests.test_game_flow import FakeGameRepo, FakeUserRepo


class FakeSponsorRepo(SponsorRepository):
    async def list_active(self) -> list[SponsorRecord]:
        return []


@pytest.fixture
def game_api_client(translator: object) -> TestClient:
    container = AppContainer.build(
        session_backend="memory",
        init_db=False,
        user_repo=FakeUserRepo(lang="en"),
        game_repo=FakeGameRepo(),
        sponsor_repo=FakeSponsorRepo(),
    )
    app = FastAPI()
    app.include_router(games_router)
    app.state.container = container
    return TestClient(app)


def test_api_create_join_move(game_api_client: TestClient) -> None:
    create = game_api_client.post(
        "/games",
        json={
            "creator": {"id": 1, "first_name": "Alice", "username": "alice", "lang_code": "en"},
            "game_type": int(GameTypeId.CONNECT_4),
            "inline_message_id": "inline-api",
            "lang": "en",
        },
    )
    assert create.status_code == 201
    game_id = create.json()["game_id"]

    join = game_api_client.post(
        f"/games/{game_id}/join",
        json={"player": {"id": 2, "first_name": "Bob", "username": "bob", "lang_code": "en"}, "lang": "en"},
    )
    assert join.status_code == 200
    assert len(join.json()["board"]["players"]) == 2

    move = game_api_client.post(
        f"/games/{game_id}/move",
        json={"player_id": 1, "row": 0, "col": 1, "lang": "en"},
    )
    assert move.status_code == 200
    assert move.json()["view"]["board"]["game_id"] == game_id

    state = game_api_client.get(f"/games/{game_id}")
    assert state.status_code == 200
