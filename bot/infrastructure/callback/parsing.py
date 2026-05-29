from __future__ import annotations

from bot.domain.schemas.game import GameTypeId
from bot.infrastructure.callback.payloads import MakeGameCallback

_MAKE_GAME_PREFIX = MakeGameCallback.__prefix__


def parse_make_game_callback(raw: str | None) -> MakeGameCallback | None:
    """Parse make-game callback_data, including legacy 3-part payloads."""
    if not raw or not raw.startswith(f"{_MAKE_GAME_PREFIX}:"):
        return None
    parts = raw.split(":")
    try:
        if len(parts) == 3:
            _, creator_id, game_type = parts
            return MakeGameCallback(
                creator_id=int(creator_id),
                game_type=GameTypeId(int(game_type)),
                mine_count=0,
            )
        if len(parts) == 4:
            return MakeGameCallback.unpack(raw)
    except (ValueError, TypeError):
        return None
    return None
