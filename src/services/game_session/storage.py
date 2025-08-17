from abc import ABC, abstractmethod
from typing import TypeVar, Dict, Optional

GameUI = TypeVar('GameUI')
GameId = TypeVar('GameId')


class BaseStorage(ABC):
    @abstractmethod
    def get(self, game_id: GameId) -> Optional[GameUI]:
        pass
    
    @abstractmethod
    def push(self, game_id: GameId) -> None:
        pass
    
    @abstractmethod
    def delete(self, game_id: GameId) -> None:
        pass
    
    
class InMemoryStorage(BaseStorage):
    def __init__(self):
        self.games: Dict[GameId, GameUI] = {}
        
    def get(self, game_id: GameId) -> Optional[GameUI]:
        return self.games.get(game_id)
    
    def push(self, game_id: GameId, game_ui: GameUI) -> None:
        self.games[game_id] = game_ui
    
    def delete(self, game_id: GameId) -> None:
        self.games.pop(game_id)