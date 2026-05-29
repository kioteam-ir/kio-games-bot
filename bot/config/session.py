from pydantic import Field

from bot.config.base import BaseConfig


class SessionConfigClass(BaseConfig):
    game_session_timeout_seconds: float = Field(
        default=300.0,
        alias="GAME_SESSION_TIMEOUT",
    )
    inline_query_cache_time: int = Field(default=0, alias="INLINE_QUERY_CACHE_TIME")


SessionConfig = SessionConfigClass()  # type: ignore[call-arg]

__all__ = ("SessionConfig", "SessionConfigClass")
