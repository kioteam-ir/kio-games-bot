from __future__ import annotations

from typing import NoReturn

from fastapi import APIRouter, HTTPException, status

from api.presentation.dependencies import GameFlowDep, SessionManagerDep
from api.presentation.schemas.games import (
    ApiErrorResponse,
    CreateGameBody,
    CreateGameResponse,
    GameBoardResponse,
    JoinGameBody,
    MoveGameBody,
    MoveGameResponse,
)
from bot.application.dto.game import (
    GameBoardView,
    JoinGameRequest,
    MakeGameRequest,
    MoveGameRequest,
    UseCaseError,
)

router = APIRouter(prefix="/games", tags=["games"])


def _board_response(view: GameBoardView) -> GameBoardResponse:
    return GameBoardResponse(
        text=view.text,
        game_id=view.game_id,
        game_over=view.game_over,
        board=view.board,
    )


def _raise_use_case(error: UseCaseError) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=ApiErrorResponse(message_key=error.message_key.value, alert=error.alert).model_dump(),
    )


@router.post("", response_model=CreateGameResponse, status_code=status.HTTP_201_CREATED)
async def create_game(body: CreateGameBody, game_flow: GameFlowDep) -> CreateGameResponse:
    result = await game_flow.create(
        MakeGameRequest(
            creator=body.creator,
            game_type=body.game_type,
            inline_message_id=body.inline_message_id,
            lang=body.lang,
        )
    )
    if isinstance(result, UseCaseError):
        _raise_use_case(result)
    return CreateGameResponse(game_id=result.game_id, text=result.text)


@router.get("/{game_id}", response_model=GameBoardResponse)
async def get_game_state(game_id: int, game_flow: GameFlowDep) -> GameBoardResponse:
    result = await game_flow.get_state(game_id)
    if isinstance(result, UseCaseError):
        _raise_use_case(result)
    return _board_response(result)


@router.post("/{game_id}/join", response_model=GameBoardResponse)
async def join_game(game_id: int, body: JoinGameBody, game_flow: GameFlowDep) -> GameBoardResponse:
    result = await game_flow.join(JoinGameRequest(player=body.player, game_id=game_id, lang=body.lang))
    if isinstance(result, UseCaseError):
        _raise_use_case(result)
    return _board_response(result.view)


@router.post("/{game_id}/move", response_model=MoveGameResponse)
async def move_game(
    game_id: int,
    body: MoveGameBody,
    game_flow: GameFlowDep,
    session_manager: SessionManagerDep,
) -> MoveGameResponse:
    result = await game_flow.move(
        MoveGameRequest(
            player_id=body.player_id,
            game_id=game_id,
            row=body.row,
            col=body.col,
            lang=body.lang,
        )
    )
    if isinstance(result, UseCaseError):
        _raise_use_case(result)
    if result.should_delete_session:
        await session_manager.delete(game_id)
    return MoveGameResponse(
        view=_board_response(result.view),
        match_summary=result.match_summary,
        should_delete_session=result.should_delete_session,
    )
