from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Awaitable, Callable
from contextlib import suppress
from time import monotonic
from uuid import uuid4

from bot.domain.entities.game_session import GameSession


class GameSessionStorage(ABC):
    @abstractmethod
    def get(self, game_id: int) -> GameSession | None: ...

    @abstractmethod
    def push(self, game_id: int, session: GameSession) -> None: ...

    @abstractmethod
    def delete(self, game_id: int) -> None: ...


class InMemoryGameSessionStorage(GameSessionStorage):
    def __init__(self) -> None:
        self._sessions: dict[int, GameSession] = {}

    def get(self, game_id: int) -> GameSession | None:
        return self._sessions.get(game_id)

    def push(self, game_id: int, session: GameSession) -> None:
        self._sessions[game_id] = session

    def delete(self, game_id: int) -> None:
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

    def get(self, game_id: int) -> GameSession | None:
        session = self._storage.get(game_id)
        if session is not None:
            self._last_accessed[game_id] = monotonic()
        return session

    def push(self, session: GameSession) -> int:
        game_id = uuid4().int % (10**18)
        self._storage.push(game_id, session)
        self._last_accessed[game_id] = monotonic()
        return game_id

    async def delete(self, game_id: int) -> None:
        session = self._storage.get(game_id)
        for handler in self._listeners.get("session_deleted", []):
            if session is not None:
                with suppress(Exception):
                    await handler(game_id, session)
        self._storage.delete(game_id)
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
