from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Awaitable, Callable
from contextlib import suppress
from time import monotonic
from uuid import uuid4

from bot.application.services.game_catalog import GameCatalogService
from bot.domain.entities.game_session import GameSession
from bot.domain.schemas.session_store import StoredGameSession, from_stored_session, to_stored_session


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
    def __init__(self, storage: GameSessionStorage, timeout: float) -> None:
        self._storage = storage
        self._timeout = timeout
        self._last_accessed: dict[int, float] = {}
        self._listeners: dict[str, list[SessionDeletedHandler]] = defaultdict(list)
        self._lock = asyncio.Lock()

    def subscribe(self, event_name: str, handler: SessionDeletedHandler) -> None:
        self._listeners[event_name].append(handler)

    async def get(self, game_id: int) -> GameSession | None:
        session = await self._storage.get(game_id)
        if session is not None:
            self._last_accessed[game_id] = monotonic()
        return session

    async def push(self, session: GameSession) -> int:
        game_id = uuid4().int % (10**18)
        await self._storage.set(game_id, session)
        self._last_accessed[game_id] = monotonic()
        return game_id

    async def save(self, game_id: int, session: GameSession) -> None:
        await self._storage.set(game_id, session)
        self._last_accessed[game_id] = monotonic()

    async def delete(self, game_id: int) -> None:
        session = await self._storage.get(game_id)
        for handler in self._listeners.get("session_deleted", []):
            if session is not None:
                with suppress(Exception):
                    await handler(game_id, session)
        await self._storage.delete(game_id)
        self._last_accessed.pop(game_id, None)

    async def start_cleanup_loop(self) -> None:
        while True:
            await asyncio.sleep(self._timeout / 2)
            async with self._lock:
                now = monotonic()
                expired = [
                    game_id
                    for game_id, last_time in self._last_accessed.items()
                    if now - last_time > self._timeout
                ]
            for game_id in expired:
                await self.delete(game_id)
