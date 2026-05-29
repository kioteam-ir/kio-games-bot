from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from bot.domain.entities.game_session import GameSession


class JoinSessionError(StrEnum):
    NOT_FOUND = "not_found"
    FULL = "full"
    CREATOR = "creator"


class JoinSessionOutcome(BaseModel):
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    session: GameSession | None = None
    error: JoinSessionError | None = None
    idempotent: bool = False
