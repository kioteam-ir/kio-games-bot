from __future__ import annotations

import unittest

from bot.domain.schemas.game import GameTypeId
from bot.infrastructure.callback.payloads import (
    CellMoveCallback,
    ChangeLangCallback,
    JoinGameCallback,
    MakeGameCallback,
    PlayerInfoCallback,
)


class CallbackPayloadTests(unittest.TestCase):
    def test_change_lang_roundtrip(self) -> None:
        payload = ChangeLangCallback(lang="en")
        packed = payload.pack()
        restored = ChangeLangCallback.unpack(packed)
        self.assertEqual(restored.lang, "en")

    def test_make_game_roundtrip(self) -> None:
        payload = MakeGameCallback(creator_id=42, game_type=GameTypeId.CONNECT_4)
        restored = MakeGameCallback.unpack(payload.pack())
        self.assertEqual(restored.creator_id, 42)
        self.assertEqual(restored.game_type, GameTypeId.CONNECT_4)

    def test_join_game_roundtrip(self) -> None:
        payload = JoinGameCallback(game_id=999)
        restored = JoinGameCallback.unpack(payload.pack())
        self.assertEqual(restored.game_id, 999)

    def test_cell_move_roundtrip(self) -> None:
        payload = CellMoveCallback(row=2, col=3, game_id=7)
        restored = CellMoveCallback.unpack(payload.pack())
        self.assertEqual((restored.row, restored.col, restored.game_id), (2, 3, 7))

    def test_player_info_roundtrip(self) -> None:
        payload = PlayerInfoCallback(player_id=5, game_type=GameTypeId.XO)
        restored = PlayerInfoCallback.unpack(payload.pack())
        self.assertEqual(restored.player_id, 5)
        self.assertEqual(restored.game_type, GameTypeId.XO)
