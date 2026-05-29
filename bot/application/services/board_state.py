from __future__ import annotations

from bot.application.dto.board import BoardCell, BoardState, ColumnPickerOption, PlayerSlot
from bot.domain.entities.game_session import GameSession
from bot.domain.games.connect.with_friend import VsFriendEngine
from bot.domain.games.registry import get_game_module

_NUMBER_EMOJI: dict[int, str] = {
    0: "0️⃣",
    1: "1️⃣",
    2: "2️⃣",
    3: "3️⃣",
    4: "4️⃣",
    5: "5️⃣",
    6: "6️⃣",
    7: "7️⃣",
    8: "8️⃣",
    9: "9️⃣",
    10: "🔟",
}


class BoardStateBuilder:
    @staticmethod
    def build(session: GameSession, game_id: int, *, game_over: bool) -> BoardState:
        module = get_game_module(session.game_type)
        engine = session.game_engine
        row_models: list[tuple[BoardCell, ...]] = []
        for row_idx, row in enumerate(engine.board, start=1):
            cells: list[BoardCell] = []
            for col_idx, cell in enumerate(row, start=1):
                cells.append(
                    BoardCell(
                        row=row_idx,
                        col=col_idx,
                        label=module.cell_display(engine, cell),
                    )
                )
            row_models.append(tuple(cells))

        column_picker: tuple[ColumnPickerOption, ...] | None = None
        if module.uses_column_picker() and isinstance(engine, VsFriendEngine):
            legal = engine.legal_moves()
            column_picker = tuple(
                ColumnPickerOption(
                    col=col + 1,
                    label="🚫" if col not in legal else _NUMBER_EMOJI[col + 1],
                )
                for col in range(engine.cols)
            )

        players: tuple[PlayerSlot, ...] = ()
        if len(session.players) == 2:
            players = tuple(
                PlayerSlot(
                    player_id=player.id,
                    name=player.first_name,
                    is_current=player.id == session.current_player.id,
                )
                for player in session.players
            )

        return BoardState(
            game_id=game_id,
            game_type=session.game_type,
            game_over=game_over,
            rows=tuple(row_models),
            column_picker=column_picker,
            players=players,
        )
