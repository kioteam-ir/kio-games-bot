from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from api.infrastructure.database.models import AppSponser
from tools.common import (
    MigrationCliArgs,
    MigrationStats,
    build_base_parser,
    ensure_sql_exists,
    migration_session,
    parse_cli_args,
    parse_pg_bool,
    parse_pg_date,
)
from tools.schemas import LegacySponsorRow
from tools.sql_dump import parse_copy_block, row_dict

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _legacy_sponsor_from_row(raw: dict[str, str | None]) -> LegacySponsorRow:
    return LegacySponsorRow.model_validate(
        {
            "id": int(raw["id"]),  # type: ignore[arg-type]
            "link": raw["link"],
            "name": raw["name"],
            "joined_memebers": int(raw.get("joined_memebers") or 0),
            "is_active": parse_pg_bool(raw.get("is_active")),
            "created_time": parse_pg_date(raw["created_time"]),
        }
    )


async def migrate_sponsors(cli: MigrationCliArgs, stats: MigrationStats) -> None:
    block = parse_copy_block(cli.sql_path, "app_sponser")
    if block is None:
        print("No app_sponser COPY block found in dump")
        return

    if not block.rows:
        print("app_sponser COPY block is empty")
        return

    step = stats.step("sponsors")
    processed = 0

    async with migration_session(dry_run=cli.dry_run) as session:
        for raw_row in block.rows:
            if cli.limit and processed >= cli.limit:
                break
            processed += 1

            try:
                legacy = _legacy_sponsor_from_row(row_dict(block, raw_row))
                existing = await session.get(AppSponser, legacy.id)
                if existing is None:
                    session.add(
                        AppSponser(
                            id=legacy.id,
                            link=legacy.link,
                            name=legacy.name,
                            joined_memebers=legacy.joined_memebers,
                            is_active=legacy.is_active,
                            created_time=legacy.created_time,
                        )
                    )
                    step.created += 1
                    continue

                if cli.overwrite:
                    existing.link = legacy.link
                    existing.name = legacy.name
                    existing.joined_memebers = legacy.joined_memebers
                    existing.is_active = legacy.is_active
                    existing.created_time = legacy.created_time
                    step.updated += 1
                else:
                    step.skipped += 1
            except Exception as exc:  # noqa: BLE001
                step.errors += 1
                print(f"  sponsor row error: {exc}")

    print(f"Sponsors: +{step.created} ~{step.updated} skip={step.skipped} err={step.errors}")


async def main_async(cli: MigrationCliArgs) -> None:
    ensure_sql_exists(cli.sql_path)
    stats = MigrationStats()
    await migrate_sponsors(cli, stats)
    print(stats.report())


def main() -> None:
    parser = build_base_parser("Migrate app_sponser rows from kio-bot.sql dump")
    cli = parse_cli_args(parser)
    asyncio.run(main_async(cli))


if __name__ == "__main__":
    main()
