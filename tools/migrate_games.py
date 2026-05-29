from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.infrastructure.database.models import AppGame, AppUser
from tools.common import (
    MigrationCliArgs,
    MigrationStats,
    build_base_parser,
    ensure_sql_exists,
    migration_session,
    parse_cli_args,
    parse_pg_datetime,
    parse_pg_int,
)
from tools.schemas import LegacyGameRow
from tools.sql_dump import parse_copy_block, row_dict

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _legacy_game_from_row(raw: dict[str, str | None]) -> LegacyGameRow:
    return LegacyGameRow.model_validate(
        {
            "id": int(raw["id"]),  # type: ignore[arg-type]
            "mid": raw["mid"],
            "type": int(raw["type"]),  # type: ignore[arg-type]
            "result": raw["result"],
            "played_time": parse_pg_datetime(raw["played_time"]),
            "player_1_id": parse_pg_int(raw.get("player_1_id")),
            "player_2_id": parse_pg_int(raw.get("player_2_id")),
        }
    )


async def _user_exists(session: AsyncSession, user_id: int | None) -> bool:
    if user_id is None:
        return True
    return (await session.execute(select(AppUser.id).where(AppUser.id == user_id))).scalar_one_or_none() is not None


async def migrate_games(cli: MigrationCliArgs, stats: MigrationStats) -> None:
    block = parse_copy_block(cli.sql_path, "app_game")
    if block is None:
        print("No app_game COPY block found in dump")
        return

    step = stats.step("games")
    processed = 0

    async with migration_session(dry_run=cli.dry_run) as session:
        for raw_row in block.rows:
            if cli.limit and processed >= cli.limit:
                break
            processed += 1

            try:
                legacy = _legacy_game_from_row(row_dict(block, raw_row))
                if not await _user_exists(session, legacy.player_1_id):
                    step.skipped += 1
                    continue
                if not await _user_exists(session, legacy.player_2_id):
                    step.skipped += 1
                    continue

                existing = await session.get(AppGame, legacy.id)
                if existing is None:
                    session.add(
                        AppGame(
                            id=legacy.id,
                            mid=legacy.mid,
                            type=legacy.type,
                            result=legacy.result,
                            played_time=legacy.played_time,
                            player_1_id=legacy.player_1_id,
                            player_2_id=legacy.player_2_id,
                        )
                    )
                    step.created += 1
                    continue

                if cli.overwrite:
                    existing.mid = legacy.mid
                    existing.type = legacy.type
                    existing.result = legacy.result
                    existing.played_time = legacy.played_time
                    existing.player_1_id = legacy.player_1_id
                    existing.player_2_id = legacy.player_2_id
                    step.updated += 1
                else:
                    step.skipped += 1
            except Exception as exc:  # noqa: BLE001
                step.errors += 1
                print(f"  game row error: {exc}")

    print(f"Games: +{step.created} ~{step.updated} skip={step.skipped} err={step.errors}")


async def main_async(cli: MigrationCliArgs) -> None:
    ensure_sql_exists(cli.sql_path)
    stats = MigrationStats()
    await migrate_games(cli, stats)
    print(stats.report())


def main() -> None:
    parser = build_base_parser("Migrate app_game rows from kio-bot.sql dump")
    cli = parse_cli_args(parser)
    asyncio.run(main_async(cli))


if __name__ == "__main__":
    main()
