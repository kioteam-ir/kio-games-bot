"""CallbackData payloads parsed by aiogram filters."""

from __future__ import annotations

from typing import Literal

from aiogram.filters.callback_data import CallbackData

from bot.domain.schemas.game import GameTypeId

LangCode = Literal["tr", "en", "fa", "he", "ru", "zh", "ar", "de", "fr"]


class ChangeLangCallback(CallbackData, prefix="chl"):
    lang: LangCode


class PlayerInfoCallback(CallbackData, prefix="pi"):
    player_id: int
    game_type: GameTypeId


class MakeGameCallback(CallbackData, prefix="mg"):
    creator_id: int
    game_type: GameTypeId


class JoinGameCallback(CallbackData, prefix="jp"):
    game_id: int


class CellMoveCallback(CallbackData, prefix="cl"):
    row: int
    col: int
    game_id: int
