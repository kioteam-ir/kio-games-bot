"""Pydantic schemas for domain data transfer."""

from bot.domain.schemas.game import (
    GameCatalogEntry,
    GameMatchSummary,
    GameResultKind,
    GameTypeId,
    HeadToHeadStats,
    PlayerGameStats,
)
from bot.domain.schemas.player import TelegramPlayer
from bot.domain.schemas.sponsor import SponsorRecord
from bot.domain.schemas.texts import CommandKey, LocaleTexts, TextsBundle
from bot.domain.schemas.user import UserRecord

__all__ = (
    "CommandKey",
    "GameCatalogEntry",
    "GameMatchSummary",
    "GameResultKind",
    "GameTypeId",
    "HeadToHeadStats",
    "LocaleTexts",
    "PlayerGameStats",
    "SponsorRecord",
    "TelegramPlayer",
    "TextsBundle",
    "UserRecord",
)
