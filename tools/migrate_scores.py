from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from sqlalchemy import select

from api.infrastructure.database.models import AppScore, AppUser
from tools.common import (
    MigrationCliArgs,
    MigrationStats,
    build_base_parser,
    ensure_sql_exists,
    migration_session,
    parse_cli_args,
)
from tools.schemas import LegacyScoreRow
from tools.sql_dump import parse_copy_block, row_dict

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _legacy_score_from_row(raw: dict[str, str | None]) -> LegacyScoreRow:
    return LegacyScoreRow.model_validate(
        {
            "id": int(raw["id"]),  # type: ignore[arg-type]
            "games": int(raw["games"]),  # type: ignore[arg-type]
            "wins": int(raw["wins"]),  # type: ignore[arg-type]
            "losses": int(raw["losses"]),  # type: ignore[arg-type]
            "game_type": int(raw["game_type"]),  # type: ignore[arg-type]
            "user_id": int(raw["user_id"]),  # type: ignore[arg-type]
        }
    )


async def migrate_scores(cli: MigrationCliArgs, stats: MigrationStats) -> None:
    block = parse_copy_block(cli.sql_path, "app_score")
    if block is None:
        print("No app_score COPY block found in dump")
        return

    step = stats.step("scores")
    processed = 0

    async with migration_session(dry_run=cli.dry_run) as session:
        for raw_row in block.rows:
            if cli.limit and processed >= cli.limit:
                break
            processed += 1

            try:
                legacy = _legacy_score_from_row(row_dict(block, raw_row))
                user_exists = (
                    await session.execute(select(AppUser.id).where(AppUser.id == legacy.user_id))
                ).scalar_one_or_none()
                if user_exists is None:
                    step.skipped += 1
                    continue

                existing = await session.get(AppScore, legacy.id)
                if existing is None:
                    session.add(
                        AppScore(
                            id=legacy.id,
                            games=legacy.games,
                            wins=legacy.wins,
                            losses=legacy.losses,
                            game_type=legacy.game_type,
                            user_id=legacy.user_id,
                        )
                    )
                    step.created += 1
                    continue

                if cli.overwrite:
                    existing.games = legacy.games
                    existing.wins = legacy.wins
                    existing.losses = legacy.losses
                    existing.game_type = legacy.game_type
                    existing.user_id = legacy.user_id
                    step.updated += 1
                else:
                    step.skipped += 1
            except Exception as exc:  # noqa: BLE001
                step.errors += 1
                print(f"  score row error: {exc}")

    print(f"Scores: +{step.created} ~{step.updated} skip={step.skipped} err={step.errors}")


async def main_async(cli: MigrationCliArgs) -> None:
    ensure_sql_exists(cli.sql_path)
    stats = MigrationStats()
    await migrate_scores(cli, stats)
    print(stats.report())


def main() -> None:
    parser = build_base_parser("Migrate app_score rows from kio-bot.sql dump")
    cli = parse_cli_args(parser)
    asyncio.run(main_async(cli))


if __name__ == "__main__":
    main()
