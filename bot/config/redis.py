from __future__ import annotations

from pydantic import Field

from bot.config.base import BaseConfig


class RedisConfigClass(BaseConfig):
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")
    session_key_prefix: str = Field(default="kio:session:", alias="REDIS_SESSION_PREFIX")


RedisConfig = RedisConfigClass()

__all__ = ("RedisConfig", "RedisConfigClass")
