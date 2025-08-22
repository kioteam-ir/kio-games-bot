from enum import Enum
from typing import Dict, Optional


class CommandTypes(Enum):
    START = "start"
    GUIDE = "guide"
    SETTINGS = "settings"
    ABOUT = "about"
    CREATE_GAME_TEXT = 'create-game-text'
    CREATE_GAME_BUTTON = 'create-game-button'
    YOU_ARE_BANNED_TITLE = 'you-are-banned-title'
    YOU_ARE_BANNED_TEXt = 'you-are-banned-text'
    WAITING_FOR_PLAYER = 'waiting-for-player'
    IPLAY = 'i-play'
    CANNOT_PLAY_WITH_YOURSELF = 'cannot-play-with-yourself'
    NOT_YOUR_GAME = 'not-your-game'
    NOT_YOUR_TURN = 'not-your-turn'
    COLUMN_FULL = 'column-full'
    PLAYER_GAME_STATS = 'player-game-stats'
    GAME_IN_PROGRESS_TEXT = 'game-in-progress-text'
    GAME_ENDED_TEXT = 'game-ended-text'
    GAME_IS_DRAW_TEXT = 'game-is-draw-text'


class CommandCache:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._cache = {}
        return cls._instance

    def set(self, lang: str, command: CommandTypes, value: str) -> None:
        if lang not in self._cache:
            self._cache[lang] = {}
        self._cache[lang][command.value] = value

    def get(self, lang: str, command: CommandTypes) -> Optional[str]:
        return self._cache.get(lang, {}).get(command.value)

    def has(self, lang: str, command: CommandTypes) -> bool:
        return command.value in self._cache.get(lang, {})

    def remove(self, lang: str, command: CommandTypes) -> None:
        if lang in self._cache and command.value in self._cache[lang]:
            del self._cache[lang][command.value]

    def all(self) -> Dict[str, Dict[str, str]]:
        return self._cache


texts_cache = CommandCache()

