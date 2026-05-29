from pydantic import Field, computed_field

from bot.config.base import BaseConfig

DEFAULT_ADMIN_IDS: tuple[int, ...] = (1369473488, 6719097274, 262253630)


def parse_admin_ids(value: object) -> list[int]:
    if value is None or value == "":
        return list(DEFAULT_ADMIN_IDS)
    if isinstance(value, int):
        return [value]
    if isinstance(value, str):
        return [int(part.strip()) for part in value.split(",") if part.strip()]
    if isinstance(value, list):
        return [int(item) for item in value]
    msg = f"Unsupported ADMIN_IDS value: {value!r}"
    raise TypeError(msg)


class BotConfigClass(BaseConfig):
    bot_token: str = Field(..., alias="TOKEN")
    admin_ids_env: str = Field(default="", alias="ADMIN_IDS")
    bot_username: str = Field(default="kiogamesbot", alias="BOT_USERNAME")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def admin_ids(self) -> list[int]:
        return parse_admin_ids(self.admin_ids_env)


BotConfig = BotConfigClass()  # type: ignore[call-arg]

__all__ = ("BotConfig", "BotConfigClass", "DEFAULT_ADMIN_IDS", "parse_admin_ids")
