"""Pure game engines and pluggable game modules."""

from bot.domain.games.base import GameEngine
from bot.domain.games.connect.with_friend import VsFriendEngine
from bot.domain.games.ports import GameFamily, GameModule
from bot.domain.games.registry import (
    create_engine,
    family_for,
    get_game_module,
    register_game_module,
)
from bot.domain.games.types import Cell, Event, Player
from bot.domain.games.XO.with_friend import VsFriendXO

__all__ = (
    "Cell",
    "Event",
    "GameEngine",
    "GameFamily",
    "GameModule",
    "Player",
    "VsFriendEngine",
    "VsFriendXO",
    "create_engine",
    "family_for",
    "get_game_module",
    "register_game_module",
)
