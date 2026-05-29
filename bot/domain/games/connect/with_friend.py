from ..base import GameEngine


class VsFriendEngine(GameEngine):
    """
    Two-human-players engine.
    - Alternates turns
    - Synchronous moves
    """

    def make_move(self, move: int | tuple[int, int]) -> bool:
        if isinstance(move, int):
            if not self.is_column_playable(move):
                return False

            row = self._get_next_row_for_col(move)
            if row is None:
                return False

            self._place_piece_at(row, move, self.current_player)
            self._finalize_move_after_placement(row, move, self.current_player)

            if not self.ended:
                self.switch_player()

            return True
        raise ValueError("connect-game only supports int moves(columns)")

    def apply_ui_move(self, *, row: int, col: int) -> bool:
        # row=0 means column-picker row in Telegram UI
        if row != 0:
            return False
        return self.make_move(col - 1)
