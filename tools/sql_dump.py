from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_COPY_HEADER = re.compile(
    r"^COPY public\.(?P<table>[a-z_]+) \((?P<columns>[^)]+)\) FROM stdin;$"
)


@dataclass(frozen=True, slots=True)
class CopyBlock:
    table: str
    columns: tuple[str, ...]
    rows: tuple[tuple[str | None, ...], ...]


def split_copy_line(line: str) -> tuple[str | None, ...]:
    return tuple(None if part == "\\N" else part for part in line.split("\t"))


def parse_copy_block(sql_path: Path, table: str) -> CopyBlock | None:
    lines = sql_path.read_text(encoding="utf-8").splitlines()
    collecting = False
    columns: tuple[str, ...] = ()
    rows: list[tuple[str | None, ...]] = []

    for line in lines:
        if not collecting:
            match = _COPY_HEADER.match(line)
            if match and match.group("table") == table:
                columns = tuple(part.strip() for part in match.group("columns").split(","))
                collecting = True
            continue

        if line == r"\.":
            return CopyBlock(table=table, columns=columns, rows=tuple(rows))

        if line.strip():
            rows.append(split_copy_line(line))

    return None


def row_dict(block: CopyBlock, row: tuple[str | None, ...]) -> dict[str, str | None]:
    return dict(zip(block.columns, row, strict=True))
