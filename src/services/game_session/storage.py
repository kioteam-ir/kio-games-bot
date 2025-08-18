from abc import ABC, abstractmethod
from typing import TypeVar, Dict, Optional
from bot.gameUI import GameUI



class BaseStorage(ABC):
    @abstractmethod
    def get(self, game_id: int) -> Optional[GameUI]:
        pass
    
    @abstractmethod
    def push(self, game_id: int) -> None:
        pass
    
    @abstractmethod
    def delete(self, game_id: int) -> None:
        pass
    
    
class InMemoryStorage(BaseStorage):
    def __init__(self):
        self.games: Dict[int, GameUI] = {}
        
    def get(self, game_id: int) -> Optional[GameUI]:
        return self.games.get(game_id)
    
    def push(self, game_id: int, game_ui: GameUI) -> None:
        self.games[game_id] = game_ui
        print(f"games : {self.games}")
    
    def delete(self, game_id: int) -> None:
        self.games.pop(game_id)