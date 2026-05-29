"""Build and parse callback_data via aiogram CallbackData."""

from __future__ import annotations

from bot.infrastructure.callback.payloads import (
    CellMoveCallback,
    ChangeLangCallback,
    JoinGameCallback,
    MakeGameCallback,
    PlayerInfoCallback,
)

CallbackPayload = (
    ChangeLangCallback
    | PlayerInfoCallback
    | MakeGameCallback
    | JoinGameCallback
    | CellMoveCallback
)


class CallbackService:
    @staticmethod
    def parse(raw: str | None) -> CallbackPayload | None:
        if not raw:
            return None
        for payload_cls in (
            ChangeLangCallback,
            PlayerInfoCallback,
            MakeGameCallback,
            JoinGameCallback,
            CellMoveCallback,
        ):
            try:
                return payload_cls.unpack(raw)
            except ValueError:
                continue
        return None

    @staticmethod
    def build_change_lang(lang: str) -> str:
        return ChangeLangCallback(lang=lang).pack()  # type: ignore[arg-type]

    @staticmethod
    def build_player_info(player_id: int, game_type: int) -> str:
        from bot.domain.schemas.game import GameTypeId

        return PlayerInfoCallback(
            player_id=player_id,
            game_type=GameTypeId(game_type),
        ).pack()

    @staticmethod
    def build_make_game(creator_id: int, game_type: int) -> str:
        from bot.domain.schemas.game import GameTypeId

        return MakeGameCallback(
            creator_id=creator_id,
            game_type=GameTypeId(game_type),
        ).pack()

    @staticmethod
    def build_join_game(game_id: int) -> str:
        return JoinGameCallback(game_id=game_id).pack()

    @staticmethod
    def build_cell_move(row: int, col: int, game_id: int) -> str:
        return CellMoveCallback(row=row, col=col, game_id=game_id).pack()
