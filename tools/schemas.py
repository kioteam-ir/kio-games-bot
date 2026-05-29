from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

SUPPORTED_LANGS: frozenset[str] = frozenset({"tr", "en", "fa", "he", "ru", "zh", "ar", "de", "fr", "ku", "hi", "ps"})
LEGACY_LANG_MAP: dict[str, str] = {}


def normalize_lang_code(value: str) -> str:
    mapped = LEGACY_LANG_MAP.get(value, value)
    if mapped in SUPPORTED_LANGS:
        return mapped
    return "en"


class LegacyUserRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int
    joined_time: datetime
    is_superuser: bool
    is_banned: bool
    lang_code: str
    name: str = Field(default="WithOUtUsernName")
    username: str = Field(default="WithOUtName")

    @field_validator("lang_code", mode="before")
    @classmethod
    def normalize_lang(cls, value: object) -> str:
        if not isinstance(value, str):
            msg = f"lang_code must be str, got {type(value)!r}"
            raise TypeError(msg)
        return normalize_lang_code(value)


class LegacyGameRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int
    mid: str
    type: int
    result: Literal["player_1", "player_2", "draw"]
    played_time: datetime
    player_1_id: int | None = None
    player_2_id: int | None = None


class LegacyScoreRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int
    games: int
    wins: int
    losses: int
    game_type: int
    user_id: int


class LegacySponsorRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int
    link: str
    name: str
    joined_memebers: int = 0
    is_active: bool = True
    created_time: date


class SponsorInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int
    name: str
    link: str
    is_active: bool = True
    joined_memebers: int = 0


class LangCodeUpdate(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: int
    old_lang: str
    new_lang: str
