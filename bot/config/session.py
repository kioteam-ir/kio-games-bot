from __future__ import annotations

from typing import Literal

from pydantic import Field

from bot.config.base import BaseConfig


class SessionConfigClass(BaseConfig):
    game_session_timeout_seconds: float = Field(
        default=300.0,
        alias="GAME_SESSION_TIMEOUT",
    )
    session_cleanup_batch_size: int = Field(default=50, alias="SESSION_CLEANUP_BATCH_SIZE")
    session_cleanup_interval_seconds: float = Field(default=0.0, alias="SESSION_CLEANUP_INTERVAL")
    session_expiry_grace_seconds: float = Field(default=120.0, alias="SESSION_EXPIRY_GRACE")
    inline_query_cache_time: int = Field(default=30, alias="INLINE_QUERY_CACHE_TIME")
    callback_idempotency_ttl_seconds: int = Field(default=300, alias="CALLBACK_IDEMPOTENCY_TTL")
    session_backend: Literal["memory", "redis"] = Field(default="redis", alias="SESSION_BACKEND")


SessionConfig = SessionConfigClass()

__all__ = ("SessionConfig", "SessionConfigClass")
