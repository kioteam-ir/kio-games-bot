from __future__ import annotations

from typing import Any

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery

from bot.infrastructure.callback.parsing import parse_make_game_callback


class MakeGameCallbackFilter(BaseFilter):
    async def __call__(
        self,
        callback: CallbackQuery,
        **kwargs: Any,
    ) -> bool | dict[str, Any]:
        _ = kwargs
        parsed = parse_make_game_callback(callback.data)
        if parsed is None:
            return False
        return {"callback_data": parsed}
