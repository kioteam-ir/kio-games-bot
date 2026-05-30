from __future__ import annotations

from redis.asyncio import Redis

from bot.application.services.game_catalog import GameCatalogService
from bot.application.services.session_manager import GameSessionStorage, InMemoryGameSessionStorage
from bot.config.redis import RedisConfigClass
from bot.config.session import SessionConfigClass
from bot.infrastructure.session.redis_storage import RedisGameSessionStorage


def build_session_storage(
    session_config: SessionConfigClass,
    catalog: GameCatalogService,
    redis_config: RedisConfigClass | None = None,
    redis_client: Redis | None = None,
) -> tuple[GameSessionStorage, Redis | None]:
    if session_config.session_backend == "redis":
        cfg = redis_config or RedisConfigClass()
        client = redis_client or Redis.from_url(cfg.redis_url, decode_responses=False)
        storage: GameSessionStorage = RedisGameSessionStorage(
            client,
            catalog,
            key_prefix=cfg.session_key_prefix,
            ttl_seconds=int(session_config.game_session_timeout_seconds),
            grace_seconds=session_config.session_expiry_grace_seconds,
        )
        return storage, client
    return InMemoryGameSessionStorage(), None
