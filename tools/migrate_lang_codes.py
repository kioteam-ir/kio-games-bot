from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from pydantic import BaseModel
from sqlalchemy import select, update

from api.infrastructure.database.models import AppUser
from tools.common import MigrationStats, migration_session
from tools.schemas import LEGACY_LANG_MAP, SUPPORTED_LANGS, LangCodeUpdate, normalize_lang_code

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


class LangMigrationArgs(BaseModel):
    dry_run: bool = False
    only_legacy: bool = True


async def migrate_lang_codes(args: LangMigrationArgs, stats: MigrationStats) -> list[LangCodeUpdate]:
    step = stats.step("lang_codes")
    updates: list[LangCodeUpdate] = []

    async with migration_session(dry_run=args.dry_run) as session:
        result = await session.execute(select(AppUser))
        users = result.scalars().all()

        for user in users:
            normalized = normalize_lang_code(user.lang_code)
            if normalized == user.lang_code:
                step.skipped += 1
                continue
            if args.only_legacy and user.lang_code not in LEGACY_LANG_MAP and user.lang_code in SUPPORTED_LANGS:
                step.skipped += 1
                continue

            updates.append(
                LangCodeUpdate(
                    user_id=user.id,
                    old_lang=user.lang_code,
                    new_lang=normalized,
                )
            )
            await session.execute(update(AppUser).where(AppUser.id == user.id).values(lang_code=normalized))
            step.updated += 1
            print(f"  user {user.id}: {user.lang_code} -> {normalized}")

    print(f"Lang codes: ~{step.updated} skip={step.skipped}")
    return updates


async def main_async(args: LangMigrationArgs) -> None:
    stats = MigrationStats()
    await migrate_lang_codes(args, stats)
    print(stats.report())


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize legacy lang_code values (ru -> tr)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--all-unsupported",
        action="store_true",
        help="Also map unsupported codes to en (default: only legacy ru -> tr)",
    )
    ns = parser.parse_args()
    args = LangMigrationArgs(dry_run=ns.dry_run, only_legacy=not ns.all_unsupported)
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
