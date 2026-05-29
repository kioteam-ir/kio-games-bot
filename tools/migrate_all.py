from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from tools.common import MigrationCliArgs, MigrationStats, build_base_parser, ensure_sql_exists, parse_cli_args
from tools.migrate_games import migrate_games
from tools.migrate_lang_codes import LangMigrationArgs, migrate_lang_codes
from tools.migrate_scores import migrate_scores
from tools.migrate_sequences import migrate_sequences
from tools.migrate_sponsors import migrate_sponsors
from tools.migrate_users import migrate_users

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

MIGRATION_STEPS: tuple[str, ...] = (
    "users",
    "sponsors",
    "games",
    "scores",
    "lang_codes",
    "sequences",
)


async def migrate_all(cli: MigrationCliArgs) -> MigrationStats:
    ensure_sql_exists(cli.sql_path)
    stats = MigrationStats()

    print(f"\n{'=' * 65}")
    print(f"  Kio data migration from {cli.sql_path.name}")
    print(f"  dry_run={cli.dry_run} overwrite={cli.overwrite}")
    print(f"{'=' * 65}\n")

    print("[1/6] users...")
    await migrate_users(cli, stats)

    print("\n[2/6] sponsors...")
    await migrate_sponsors(cli, stats)

    print("\n[3/6] games...")
    await migrate_games(cli, stats)

    print("\n[4/6] scores...")
    await migrate_scores(cli, stats)

    print("\n[5/6] lang_codes...")
    await migrate_lang_codes(LangMigrationArgs(dry_run=cli.dry_run), stats)

    print("\n[6/6] sequences...")
    await migrate_sequences(dry_run=cli.dry_run, stats=stats)

    return stats


async def main_async(cli: MigrationCliArgs) -> None:
    stats = await migrate_all(cli)
    print(stats.report())
    if cli.dry_run:
        print("\nDry run complete — no changes committed.")


def main() -> None:
    parser = build_base_parser("Run all Kio data migrations from kio-bot.sql")
    cli = parse_cli_args(parser)
    asyncio.run(main_async(cli))


if __name__ == "__main__":
    main()
