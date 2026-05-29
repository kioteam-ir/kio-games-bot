from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from api.infrastructure.database.models import AppUser
from tools.common import (
    MigrationCliArgs,
    MigrationStats,
    build_base_parser,
    ensure_sql_exists,
    migration_session,
    parse_cli_args,
    parse_pg_bool,
    parse_pg_datetime,
)
from tools.schemas import LegacyUserRow
from tools.sql_dump import parse_copy_block, row_dict

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _legacy_user_from_row(raw: dict[str, str | None]) -> LegacyUserRow:
    return LegacyUserRow.model_validate(
        {
            "id": int(raw["id"]),  # type: ignore[arg-type]
            "joined_time": parse_pg_datetime(raw["joined_time"]),
            "is_superuser": parse_pg_bool(raw["is_superuser"]),
            "is_banned": parse_pg_bool(raw["is_banned"]),
            "lang_code": raw["lang_code"],
            "name": raw.get("name") or "WithOUtUsernName",
            "username": raw.get("username") or "WithOUtName",
        }
    )


async def migrate_users(cli: MigrationCliArgs, stats: MigrationStats) -> None:
    block = parse_copy_block(cli.sql_path, "app_user")
    if block is None:
        print("No app_user COPY block found in dump")
        return

    step = stats.step("users")
    processed = 0

    async with migration_session(dry_run=cli.dry_run) as session:
        for raw_row in block.rows:
            if cli.limit and processed >= cli.limit:
                break
            processed += 1

            try:
                legacy = _legacy_user_from_row(row_dict(block, raw_row))
                existing = await session.get(AppUser, legacy.id)

                if existing is None:
                    session.add(
                        AppUser(
                            id=legacy.id,
                            joined_time=legacy.joined_time,
                            is_superuser=legacy.is_superuser,
                            is_banned=legacy.is_banned,
                            lang_code=legacy.lang_code,
                            name=legacy.name,
                            username=legacy.username,
                        )
                    )
                    step.created += 1
                    continue

                if cli.overwrite:
                    existing.joined_time = legacy.joined_time
                    existing.is_superuser = legacy.is_superuser
                    existing.is_banned = legacy.is_banned
                    existing.lang_code = legacy.lang_code
                    existing.name = legacy.name
                    existing.username = legacy.username
                    step.updated += 1
                    continue

                changed = False
                if existing.lang_code != legacy.lang_code:
                    existing.lang_code = legacy.lang_code
                    changed = True
                if existing.name in {"", "WithOUtUsernName"} and legacy.name != "WithOUtUsernName":
                    existing.name = legacy.name
                    changed = True
                if existing.username in {"", "WithOUtName"} and legacy.username != "WithOUtName":
                    existing.username = legacy.username
                    changed = True

                if changed:
                    step.updated += 1
                else:
                    step.skipped += 1
            except Exception as exc:  # noqa: BLE001
                step.errors += 1
                print(f"  user row error: {exc}")

    print(f"Users: +{step.created} ~{step.updated} skip={step.skipped} err={step.errors}")


async def main_async(cli: MigrationCliArgs) -> None:
    ensure_sql_exists(cli.sql_path)
    stats = MigrationStats()
    await migrate_users(cli, stats)
    print(stats.report())


def main() -> None:
    parser = build_base_parser("Migrate app_user rows from kio-bot.sql dump")
    cli = parse_cli_args(parser)
    asyncio.run(main_async(cli))


if __name__ == "__main__":
    main()
