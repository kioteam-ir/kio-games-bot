from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from bot.config.base import BaseConfig


class RateLimitAlgorithm(StrEnum):
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"


class RateLimitRule(BaseModel):
    model_config = ConfigDict(frozen=True)

    algorithm: RateLimitAlgorithm
    max_requests: int
    window_seconds: int
    capacity: int | None = None
    refill_per_second: float | None = None


class RateLimitConfigClass(BaseConfig):
    enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    key_prefix: str = Field(default="kio:rl:", alias="RATE_LIMIT_KEY_PREFIX")

    callback_move: RateLimitRule = Field(
        default_factory=lambda: RateLimitRule(
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
            max_requests=20,
            window_seconds=1,
            capacity=20,
            refill_per_second=8.0,
        )
    )
    callback_create: RateLimitRule = Field(
        default_factory=lambda: RateLimitRule(
            algorithm=RateLimitAlgorithm.FIXED_WINDOW,
            max_requests=5,
            window_seconds=300,
        )
    )
    callback_join: RateLimitRule = Field(
        default_factory=lambda: RateLimitRule(
            algorithm=RateLimitAlgorithm.FIXED_WINDOW,
            max_requests=10,
            window_seconds=60,
        )
    )
    callback_default: RateLimitRule = Field(
        default_factory=lambda: RateLimitRule(
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
            max_requests=30,
            window_seconds=60,
        )
    )
    inline_query: RateLimitRule = Field(
        default_factory=lambda: RateLimitRule(
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
            max_requests=25,
            window_seconds=1,
            capacity=25,
            refill_per_second=12.0,
        )
    )
    message: RateLimitRule = Field(
        default_factory=lambda: RateLimitRule(
            algorithm=RateLimitAlgorithm.FIXED_WINDOW,
            max_requests=12,
            window_seconds=60,
        )
    )
    sponsor_check: RateLimitRule = Field(
        default_factory=lambda: RateLimitRule(
            algorithm=RateLimitAlgorithm.FIXED_WINDOW,
            max_requests=2,
            window_seconds=30,
        )
    )


RateLimitConfig = RateLimitConfigClass()

__all__ = ("RateLimitAlgorithm", "RateLimitConfig", "RateLimitConfigClass", "RateLimitRule")
