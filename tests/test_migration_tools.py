from __future__ import annotations

from pathlib import Path

import pytest

from tools.schemas import normalize_lang_code
from tools.sql_dump import parse_copy_block, row_dict, split_copy_line

SQL_DUMP = Path("kio-bot.sql")


def test_split_copy_line_null() -> None:
    assert split_copy_line("1\t\\N\tfa") == ("1", None, "fa")


def test_parse_app_user_copy_block() -> None:
    block = parse_copy_block(SQL_DUMP, "app_user")
    assert block is not None
    assert block.table == "app_user"
    assert "lang_code" in block.columns
    assert len(block.rows) >= 100


def test_parse_app_game_copy_block() -> None:
    block = parse_copy_block(SQL_DUMP, "app_game")
    assert block is not None
    assert len(block.rows) >= 500


def test_row_dict_matches_columns() -> None:
    block = parse_copy_block(SQL_DUMP, "app_user")
    assert block is not None
    first = block.rows[0]
    data = row_dict(block, first)
    assert set(data) == set(block.columns)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("ru", "tr"),
        ("fa", "fa"),
        ("en", "en"),
        ("tr", "tr"),
        ("de", "en"),
    ],
)
def test_normalize_lang_code(raw: str, expected: str) -> None:
    assert normalize_lang_code(raw) == expected
