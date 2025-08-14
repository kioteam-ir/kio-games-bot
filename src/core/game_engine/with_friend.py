from .base import GameEngine
from .types import Player


class VsFriendEngine(GameEngine):
    """
    Two-human-players engine.
    - Alternates turns
    - Synchronous moves
    """

    def make_move(self, col: int) -> bool:
        if not self.is_column_playable(col):
            return False

        row = self._get_next_row_for_col(col)
        if row is None:
            return False

        self._place_piece_at(row, col, self.current_player)
        self._finalize_move_after_placement(row, col, self.current_player)

        if not self.ended:
            self.switch_player()

        return True
