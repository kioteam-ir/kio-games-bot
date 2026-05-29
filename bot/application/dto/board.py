from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from bot.domain.schemas.game import GameTypeId


class BoardCell(BaseModel):
    model_config = ConfigDict(frozen=True)

    row: int
    col: int
    label: str


class ColumnPickerOption(BaseModel):
    model_config = ConfigDict(frozen=True)

    col: int
    label: str


class PlayerSlot(BaseModel):
    model_config = ConfigDict(frozen=True)

    player_id: int
    name: str
    is_current: bool


class BoardState(BaseModel):
    model_config = ConfigDict(frozen=True)

    game_id: int
    game_type: GameTypeId
    game_over: bool
    rows: tuple[tuple[BoardCell, ...], ...]
    column_picker: tuple[ColumnPickerOption, ...] | None = None
    players: tuple[PlayerSlot, ...] = ()
