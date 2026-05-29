from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from sqlalchemy import text

from tools.common import MigrationStats, migration_session

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

SEQUENCE_TABLES: tuple[tuple[str, str], ...] = (
    ("app_game", "id"),
    ("app_score", "id"),
)


async def migrate_sequences(*, dry_run: bool, stats: MigrationStats) -> None:
    step = stats.step("sequences")

    async with migration_session(dry_run=dry_run) as session:
        for table, column in SEQUENCE_TABLES:
            sql = text(
                f"""
                SELECT setval(
                    pg_get_serial_sequence('{table}', '{column}'),
                    COALESCE((SELECT MAX({column}) FROM {table}), 1)
                )
                """
            )
            await session.execute(sql)
            step.updated += 1
            print(f"  reset sequence for {table}.{column}")

    print(f"Sequences: ~{step.updated}")


async def main_async(*, dry_run: bool) -> None:
    stats = MigrationStats()
    await migrate_sequences(dry_run=dry_run, stats=stats)
    print(stats.report())


def main() -> None:
    parser = argparse.ArgumentParser(description="Reset PostgreSQL sequences after data import")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(main_async(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
