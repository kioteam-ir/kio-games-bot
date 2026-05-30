from __future__ import annotations

from enum import StrEnum
from typing import Protocol

from bot.domain.games.base import GameEngine
from bot.domain.games.move_outcome import MoveRejectReason
from bot.domain.schemas.game import GameCatalogEntry, GameTypeId


class GameFamily(StrEnum):
    """Board interaction model — new games add a family or reuse one."""

    CONNECT_DROP = "connect_drop"
    GRID_MARK = "grid_mark"
    MINES = "mines"


class GameEngineFactory(Protocol):
    def __call__(self, entry: GameCatalogEntry) -> GameEngine: ...


class GameModule(Protocol):
    """Plugin contract for a playable game type."""

    @property
    def game_type_id(self) -> GameTypeId: ...

    @property
    def family(self) -> GameFamily: ...

    def create_engine(self, entry: GameCatalogEntry, *, mine_count: int | None = None) -> GameEngine: ...

    def apply_ui_move(self, engine: GameEngine, *, row: int, col: int) -> bool:
        """Apply a 1-indexed Telegram grid callback. Return False when illegal."""

    def classify_ui_move(self, engine: GameEngine, *, row: int, col: int) -> MoveRejectReason | None:
        """Return a reject reason when the move is illegal, otherwise None."""

    def try_ui_move(self, engine: GameEngine, *, row: int, col: int) -> MoveRejectReason | None:
        reason = self.classify_ui_move(engine, row=row, col=col)
        if reason is not None:
            return reason
        if not self.apply_ui_move(engine, row=row, col=col):
            return MoveRejectReason.INVALID
        return None

    def cell_display(self, engine: GameEngine, cell: object) -> str:
        """Render one board cell for inline keyboard labels."""

    def uses_column_picker(self) -> bool:
        """Whether to show the extra column-selector row (Connect-style)."""
