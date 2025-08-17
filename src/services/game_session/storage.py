from abc import ABC, abstractmethod

class BaseStorage(ABC):
    @abstractmethod
    def get(self, game_id: int) -> any:
        pass