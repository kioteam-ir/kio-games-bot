"""Application configuration via pydantic-settings."""

from bot.config.base import BaseConfig
from bot.config.bot import BotConfig, BotConfigClass
from bot.config.database import DatabaseConfig, DatabaseConfigClass
from bot.config.i18n import I18nConfig, I18nConfigClass
from bot.config.session import SessionConfig, SessionConfigClass

__all__ = (
    "BaseConfig",
    "BotConfig",
    "BotConfigClass",
    "DatabaseConfig",
    "DatabaseConfigClass",
    "I18nConfig",
    "I18nConfigClass",
    "SessionConfig",
    "SessionConfigClass",
)
