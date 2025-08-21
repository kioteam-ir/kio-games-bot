from ..async_task_manager.strategies.base import BaseStrategy
from .storage import InMemoryStorage, GameUI, BaseStorage
from typing import Dict, Optional, Callable, Awaitable, List, Union
from time import monotonic
from uuid import uuid4
import asyncio
from collections import defaultdict


def generate_game_id() -> int:
    return uuid4().int


class EventBus:
    """Simple async event bus that works globally (not per game_id)."""
    def __init__(self):
        self._listeners: Dict[str, List[Callable[..., Union[None, Awaitable]]]] = defaultdict(list)

    def subscribe(self, event_name: str, callback: Callable[..., Union[None, Awaitable]]) -> None:
        """Subscribe a callback (sync or async) to a specific event."""
        self._listeners[event_name].append(callback)

    async def notify(self, event_name: str, **kwargs) -> None:
        """Notify all listeners of an event."""
        for callback in self._listeners.get(event_name, []):
            result = callback(**kwargs)
            if asyncio.iscoroutine(result):
                await result


class GameSessionManager:
    def __init__(self, storage: BaseStorage, timeout: float, event_bus: Optional[EventBus] = None):
        self._last_accessed: Dict[int, float] = {}
        self._storage = storage
        self._timeout = timeout
        self._event_bus = event_bus or EventBus()
        self._lock = asyncio.Lock()

    def get(self, game_id: int) -> Optional[GameUI]:
        game_ui = self._storage.get(game_id)
        if game_ui:
            self._update_last_accessed(game_id)
        return game_ui

    def push(self, game_ui: GameUI) -> int:
        game_id = generate_game_id()
        self._storage.push(game_id, game_ui)
        self._update_last_accessed(game_id)
        return game_id

    async def delete(self, game_id: int) -> None:
        await self._event_bus.notify("session_deleted", game_id=game_id, game_ui=self._storage.get(game_id))
        self._storage.delete(game_id)
        self._last_accessed.pop(game_id, None)

    def _update_last_accessed(self, game_id: int) -> None:
        self._last_accessed[game_id] = monotonic()

    async def start_cleanup_loop(self) -> None:
        """Periodically checks for expired sessions and removes them."""
        while True:
            await asyncio.sleep(self._timeout / 2)  # check twice within timeout period
            async with self._lock:
                now = monotonic()
                expired_sessions = [
                    game_id for game_id, last_time in self._last_accessed.items()
                    if now - last_time > self._timeout
                ]
                for game_id in expired_sessions:
                    await self.delete(game_id)



session_manager = GameSessionManager(
    storage=InMemoryStorage(),
    timeout=5 * 60,  # 5 minutes
)
