from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Awaitable, Callable
from time import monotonic, time
from uuid import uuid4

from redis.asyncio import Redis

from bot.application.dto.session import JoinSessionError, JoinSessionOutcome
from bot.application.services.game_catalog import GameCatalogService
from bot.domain.entities.game_session import GameSession
from bot.domain.schemas.player import TelegramPlayer
from bot.domain.schemas.session_store import StoredGameSession, from_stored_session, to_stored_session
from bot.infrastructure.session.expiry_index import SessionExpiryIndex

logger = logging.getLogger(__name__)


class SessionCodec:
    def __init__(self, catalog: GameCatalogService) -> None:
        self._catalog = catalog

    def serialize(self, game_id: int, session: GameSession) -> str:
        return to_stored_session(session, game_id=game_id).model_dump_json()

    def deserialize(self, payload: str) -> GameSession:
        stored = StoredGameSession.model_validate_json(payload)
        entry = self._catalog.get(stored.lang, stored.game_type)
        session = from_stored_session(stored, entry)
        if not isinstance(session, GameSession):
            msg = "Stored session did not deserialize to GameSession"
            raise TypeError(msg)
        return session


class GameSessionStorage(ABC):
    @abstractmethod
    async def get(self, game_id: int) -> GameSession | None: ...

    @abstractmethod
    async def set(self, game_id: int, session: GameSession) -> None: ...

    @abstractmethod
    async def delete(self, game_id: int) -> None: ...


class InMemoryGameSessionStorage(GameSessionStorage):
    def __init__(self) -> None:
        self._sessions: dict[int, GameSession] = {}
        self._lock = asyncio.Lock()

    async def get(self, game_id: int) -> GameSession | None:
        async with self._lock:
            return self._sessions.get(game_id)

    async def set(self, game_id: int, session: GameSession) -> None:
        async with self._lock:
            self._sessions[game_id] = session

    async def delete(self, game_id: int) -> None:
        async with self._lock:
            self._sessions.pop(game_id, None)


SessionDeletedHandler = Callable[[int, GameSession], Awaitable[None]]


class GameSessionManager:
    def __init__(
        self,
        storage: GameSessionStorage,
        timeout: float,
        *,
        cleanup_batch_size: int = 50,
        cleanup_interval_seconds: float = 0.0,
        expiry_grace_seconds: float = 0.0,
        redis_client: Redis | None = None,
        session_key_prefix: str = "",
        inline_key_prefix: str = "kio:inline:",
    ) -> None:
        self._storage = storage
        self._timeout = timeout
        self._cleanup_batch_size = max(1, cleanup_batch_size)
        self._cleanup_interval_seconds = cleanup_interval_seconds
        self._expiry_grace_seconds = expiry_grace_seconds
        self._redis = redis_client
        self._session_key_prefix = session_key_prefix
        self._inline_key_prefix = inline_key_prefix
        self._expiry_index = SessionExpiryIndex(redis_client) if redis_client is not None else None
        self._inline_index: dict[str, int] = {}
        self._last_accessed: dict[int, float] = {}
        self._listeners: dict[str, list[SessionDeletedHandler]] = defaultdict(list)
        self._lock = asyncio.Lock()

    def subscribe(self, event_name: str, handler: SessionDeletedHandler) -> None:
        self._listeners[event_name].append(handler)

    async def get(self, game_id: int) -> GameSession | None:
        session = await self._storage.get(game_id)
        if session is not None:
            await self._touch(game_id)
        return session

    async def find_by_inline_message(self, inline_message_id: str) -> int | None:
        if self._redis is not None:
            raw = await self._redis.get(f"{self._inline_key_prefix}{inline_message_id}")
            if raw is None:
                return None
            if isinstance(raw, bytes):
                raw = raw.decode()
            return int(raw)
        return self._inline_index.get(inline_message_id)

    async def push(self, session: GameSession) -> int:
        game_id = uuid4().int % (10**18)
        await self._storage.set(game_id, session)
        await self._touch(game_id)
        await self._bind_inline_message(session.inline_message_id, game_id)
        return game_id

    async def try_join(self, game_id: int, player: TelegramPlayer) -> JoinSessionOutcome:
        async with self._lock:
            session = await self._storage.get(game_id)
            if session is None:
                return JoinSessionOutcome(error=JoinSessionError.NOT_FOUND)

            player_ids = {existing.id for existing in session.players}
            if player.id == session.players[0].id:
                return JoinSessionOutcome(error=JoinSessionError.CREATOR)
            if player.id in player_ids and len(session.players) == 2:
                await self._touch(game_id)
                return JoinSessionOutcome(session=session, idempotent=True)
            if len(session.players) >= 2:
                return JoinSessionOutcome(error=JoinSessionError.FULL)

            session.players.append(player)
            await self._storage.set(game_id, session)
            await self._touch(game_id)
            return JoinSessionOutcome(session=session)

    async def save(self, game_id: int, session: GameSession) -> None:
        await self._storage.set(game_id, session)
        await self._touch(game_id)

    async def delete(self, game_id: int) -> None:
        session = await self._storage.get(game_id)
        if session is not None:
            await self._unbind_inline_message(session.inline_message_id)
        await self._storage.delete(game_id)
        self._last_accessed.pop(game_id, None)
        if self._expiry_index is not None:
            await self._expiry_index.remove(game_id)

    async def expire(self, game_id: int) -> None:
        session = await self._storage.get(game_id)
        if session is None:
            if self._expiry_index is not None:
                await self._expiry_index.remove(game_id)
            self._last_accessed.pop(game_id, None)
            return

        for handler in self._listeners.get("session_deleted", []):
            try:
                await handler(game_id, session)
            except Exception:
                logger.exception("session_deleted handler failed game_id=%s", game_id)

        await self._unbind_inline_message(session.inline_message_id)
        await self._storage.delete(game_id)
        self._last_accessed.pop(game_id, None)
        if self._expiry_index is not None:
            await self._expiry_index.remove(game_id)

    async def _touch(self, game_id: int) -> None:
        if self._expiry_index is not None:
            await self._expiry_index.schedule(game_id, expires_at=time() + self._timeout)
        else:
            self._last_accessed[game_id] = monotonic()

    async def _bind_inline_message(self, inline_message_id: str, game_id: int) -> None:
        ttl = int(self._timeout + self._expiry_grace_seconds)
        if self._redis is not None:
            await self._redis.set(
                f"{self._inline_key_prefix}{inline_message_id}",
                str(game_id),
                ex=ttl,
            )
        else:
            self._inline_index[inline_message_id] = game_id

    async def _unbind_inline_message(self, inline_message_id: str) -> None:
        if self._redis is not None:
            await self._redis.delete(f"{self._inline_key_prefix}{inline_message_id}")
        else:
            self._inline_index.pop(inline_message_id, None)

    async def rebuild_expiry_index(self) -> None:
        if self._expiry_index is None or self._redis is None or not self._session_key_prefix:
            return

        cursor = 0
        while True:
            cursor, keys = await self._redis.scan(
                cursor,
                match=f"{self._session_key_prefix}*",
                count=100,
            )
            for key in keys:
                key_str = key.decode() if isinstance(key, bytes) else key
                suffix = key_str.removeprefix(self._session_key_prefix)
                try:
                    game_id = int(suffix)
                except ValueError:
                    continue
                ttl = await self._redis.ttl(key)
                expires_at = time() + self._timeout if ttl is None or ttl < 0 else time() + ttl
                await self._expiry_index.schedule(game_id, expires_at=expires_at)
            if cursor == 0:
                break

    async def start_cleanup_loop(self) -> None:
        interval = self._cleanup_interval_seconds or max(30.0, self._timeout / 2)
        while True:
            await asyncio.sleep(interval)
            expired_ids = await self.collect_expired_session_ids(limit=self._cleanup_batch_size)
            for game_id in expired_ids:
                await self.expire(game_id)

    async def collect_expired_session_ids(self, *, limit: int) -> list[int]:
        if self._expiry_index is not None:
            return await self._expiry_index.pop_due(limit=max(1, limit))

        async with self._lock:
            now = monotonic()
            expired = [game_id for game_id, last_time in self._last_accessed.items() if now - last_time > self._timeout]
        return expired[: max(1, limit)]
