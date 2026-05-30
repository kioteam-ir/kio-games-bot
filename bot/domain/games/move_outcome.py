from __future__ import annotations

from enum import StrEnum


class MoveRejectReason(StrEnum):
    COLUMN_FULL = "column_full"
    CELL_ALREADY_REVEALED = "cell_already_revealed"
    INVALID = "invalid"
