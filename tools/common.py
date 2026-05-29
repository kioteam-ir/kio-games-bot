from __future__ import annotations

import argparse
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.config.database import DatabaseConfigClass
from api.infrastructure.database.connection import get_session_factory, init_database


def parse_pg_bool(value: str | None) -> bool:
    return value == "t"


def parse_pg_int(value: str | None) -> int | None:
    if value is None:
        return None
    return int(value)


def parse_pg_datetime(value: str | None) -> datetime:
    if value is None:
        msg = "datetime value is required"
        raise ValueError(msg)
    normalized = value.strip()
    if normalized.endswith("+00"):
        normalized = f"{normalized[:-3]}+00:00"
    return datetime.fromisoformat(normalized)


def parse_pg_date(value: str | None) -> date:
    if value is None:
        msg = "date value is required"
        raise ValueError(msg)
    return date.fromisoformat(value)


class MigrationCliArgs(BaseModel):
    sql_path: Path
    dry_run: bool = False
    overwrite: bool = False
    limit: int = Field(default=0, ge=0)


@dataclass(slots=True)
class StepStats:
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: int = 0

    def merge(self, other: StepStats) -> None:
        self.created += other.created
        self.updated += other.updated
        self.skipped += other.skipped
        self.errors += other.errors


@dataclass(slots=True)
class MigrationStats:
    steps: dict[str, StepStats] = field(default_factory=dict)

    def step(self, name: str) -> StepStats:
        if name not in self.steps:
            self.steps[name] = StepStats()
        return self.steps[name]

    def report(self) -> str:
        lines = ["", "=" * 65, "  Migration report", "=" * 65]
        total = StepStats()
        for name, stats in self.steps.items():
            total.merge(stats)
            lines.append(
                f"  {name:<24} +{stats.created:<5} ~{stats.updated:<5} "
                f"skip={stats.skipped:<5} err={stats.errors}"
            )
        lines.append("-" * 65)
        lines.append(
            f"  {'TOTAL':<24} +{total.created:<5} ~{total.updated:<5} "
            f"skip={total.skipped:<5} err={total.errors}"
        )
        lines.append("=" * 65)
        return "\n".join(lines)


def build_base_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "sql_path",
        type=Path,
        nargs="?",
        default=Path("kio-bot.sql"),
        help="Path to PostgreSQL dump (default: kio-bot.sql)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview without committing")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing rows")
    parser.add_argument("--limit", type=int, default=0, help="Max rows to process (0 = all)")
    return parser


def parse_cli_args(parser: argparse.ArgumentParser) -> MigrationCliArgs:
    args = parser.parse_args()
    return MigrationCliArgs(
        sql_path=args.sql_path.expanduser().resolve(),
        dry_run=args.dry_run,
        overwrite=args.overwrite,
        limit=args.limit,
    )


def ensure_sql_exists(sql_path: Path) -> None:
    if not sql_path.is_file():
        msg = f"SQL dump not found: {sql_path}"
        raise FileNotFoundError(msg)


@asynccontextmanager
async def migration_session(*, dry_run: bool) -> AsyncIterator[AsyncSession]:
    init_database(DatabaseConfigClass())
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            if dry_run:
                await session.rollback()
            else:
                await session.commit()
        except Exception:
            await session.rollback()
            raise
