from __future__ import annotations

from redis.asyncio import Redis

from bot.application.services.game_catalog import GameCatalogService
from bot.application.services.session_manager import GameSessionStorage, SessionCodec
from bot.domain.entities.game_session import GameSession


class RedisGameSessionStorage(GameSessionStorage):
    def __init__(
        self,
        redis: Redis,
        catalog: GameCatalogService,
        *,
        key_prefix: str,
        ttl_seconds: int,
    ) -> None:
        self._redis = redis
        self._codec = SessionCodec(catalog)
        self._key_prefix = key_prefix
        self._ttl_seconds = ttl_seconds

    def _key(self, game_id: int) -> str:
        return f"{self._key_prefix}{game_id}"

    async def get(self, game_id: int) -> GameSession | None:
        payload = await self._redis.get(self._key(game_id))
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode()
        return self._codec.deserialize(str(payload))

    async def set(self, game_id: int, session: GameSession) -> None:
        await self._redis.set(
            self._key(game_id),
            self._codec.serialize(game_id, session),
            ex=self._ttl_seconds,
        )

    async def delete(self, game_id: int) -> None:
        await self._redis.delete(self._key(game_id))
