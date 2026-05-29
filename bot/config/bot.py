from pydantic import Field, field_validator

from bot.config.base import BaseConfig


class BotConfigClass(BaseConfig):
    bot_token: str = Field(..., alias="TOKEN")
    admin_ids: list[int] = Field(default_factory=list, alias="ADMIN_IDS")
    bot_username: str = Field(default="kiogamesbot", alias="BOT_USERNAME")

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, value: object) -> list[int]:
        if value is None or value == "":
            return [262253630]
        if isinstance(value, int):
            return [value]
        if isinstance(value, str):
            return [int(part.strip()) for part in value.split(",") if part.strip()]
        if isinstance(value, list):
            return [int(item) for item in value]
        msg = f"Unsupported ADMIN_IDS value: {value!r}"
        raise TypeError(msg)


BotConfig = BotConfigClass()  # type: ignore[call-arg]

__all__ = ("BotConfig", "BotConfigClass")
