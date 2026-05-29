from pathlib import Path

from pydantic import Field

from bot.config.base import BaseConfig


class I18nConfigClass(BaseConfig):
    default_lang: str = Field(default="fa", alias="DEFAULT_LANG")
    texts_path: Path = Field(default=Path("src/texts.json"), alias="TEXTS_PATH")
    supported_langs: list[str] = Field(
        default_factory=lambda: ["fa", "en", "ru"],
        alias="SUPPORTED_LANGS",
    )


I18nConfig = I18nConfigClass()

__all__ = ("I18nConfig", "I18nConfigClass")
