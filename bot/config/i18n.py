from pathlib import Path

from pydantic import Field

from bot.config.base import BaseConfig


class I18nConfigClass(BaseConfig):
    default_lang: str = Field(default="fa", alias="DEFAULT_LANG")
    domain: str = Field(default="bot", alias="I18N_DOMAIN")
    locales_path: Path = Field(default=Path("bot/locales"), alias="LOCALES_PATH")
    supported_langs: list[str] = Field(
        default_factory=lambda: ["tr", "en", "fa", "he", "ru", "zh", "ar", "de", "fr"],
        alias="SUPPORTED_LANGS",
    )


I18nConfig = I18nConfigClass()

__all__ = ("I18nConfig", "I18nConfigClass")
