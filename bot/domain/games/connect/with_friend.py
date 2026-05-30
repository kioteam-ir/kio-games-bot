from bot.domain.games.move_outcome import MoveRejectReason

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

    def classify_ui_move(self, *, row: int, col: int) -> MoveRejectReason | None:
        if col <= 0:
            return MoveRejectReason.INVALID
        target_col = col - 1
        if target_col < 0 or target_col >= self.cols:
            return MoveRejectReason.INVALID
        if self.is_column_playable(target_col):
            return None
        if self.column_heights[target_col] >= self.rows:
            return MoveRejectReason.COLUMN_FULL
        return MoveRejectReason.INVALID

    def apply_ui_move(self, *, row: int, col: int) -> bool:
        if self.classify_ui_move(row=row, col=col) is not None:
            return False
        return self.make_move(col - 1)
