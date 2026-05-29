from __future__ import annotations

import unittest

from bot.domain.games.connect.with_friend import VsFriendEngine
from bot.domain.games.types import Player


class ConnectEngineTests(unittest.TestCase):
    def test_column_drop_and_turn_switch(self) -> None:
        engine = VsFriendEngine(rows=6, cols=7, connect=4)
        self.assertTrue(engine.make_move(0))
        self.assertEqual(engine.current_player, Player.TWO)

    def test_vertical_win_in_column(self) -> None:
        engine = VsFriendEngine(rows=6, cols=7, connect=4)
        moves = [0, 1, 0, 1, 0, 1, 0]
        for col in moves:
            self.assertTrue(engine.make_move(col))
        self.assertTrue(engine.ended)
        self.assertEqual(engine.winner, Player.ONE)

    def test_full_column_rejected(self) -> None:
        engine = VsFriendEngine(rows=2, cols=1, connect=2)
        self.assertTrue(engine.make_move(0))
        self.assertTrue(engine.make_move(0))
        self.assertFalse(engine.make_move(0))

    def test_int_only_moves(self) -> None:
        engine = VsFriendEngine()
        with self.assertRaises(ValueError):
            engine.make_move((0, 0))
