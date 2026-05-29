
from ..base import GameEngine


class VsFriendXO(GameEngine):
    def __init__(self, n: int, connect: int) -> None:
        super().__init__(n, n, connect)
        
    def make_move(self, move: int | tuple[int, int]) -> bool:
        if isinstance(move, tuple):
            if not self.is_valid_move(move):
                return False
            
            self._place_piece_at(move[0], move[1], self.current_player)
            self._finalize_move_after_placement(move[0], move[1], self.current_player)
            
            if not self.ended:
                self.switch_player()
            return True
        raise ValueError("XO only supports tuple moves")

    def apply_ui_move(self, *, row: int, col: int) -> bool:
        if row <= 0 or col <= 0:
            return False
        return self.make_move((row - 1, col - 1))

    def is_valid_move(self, move: tuple[int, int]) -> bool:
        for n in move:
            if n >= self.cols or n < 0 or not self.board[move[0]][move[1]].is_empty:
                return False
        return True
    
    def pretty(self) -> str:
        rows_repr = []
        for r in range(self.rows):
            row_repr = []
            for c in range(self.cols):
                v = self.board[r][c]
                if v.is_empty:
                    row_repr.append("🔳")
                else:   # v is a Player
                    player = v.as_player
                    row_repr.append(player.as_symbol) # pyright: ignore[reportOptionalMemberAccess]
            rows_repr.append(" ".join(row_repr))
        return "\n".join(rows_repr)