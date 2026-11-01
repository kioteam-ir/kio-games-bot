#!/usr/bin/env python3
"""Remove or deactivate sponsor channels from the database."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from sqlalchemy import delete, select, update

from api.infrastructure.database.models import AppSponser
from tools.common import migration_session


def _parse_ids_json(raw: str) -> list[int]:
    data = json.loads(raw)
    if isinstance(data, list):
        ids: list[int] = []
        for item in data:
            if isinstance(item, int):
                ids.append(item)
            elif isinstance(item, str) and item.lstrip("-").isdigit():
                ids.append(int(item))
            elif isinstance(item, dict) and "id" in item:
                ids.append(int(item["id"]))
            else:
                msg = f"Invalid sponsor item: {item!r}"
                raise ValueError(msg)
        return ids
    if isinstance(data, int):
        return [data]
    msg = f"Expected list of IDs or objects, got {type(data)!r}"
    raise ValueError(msg)


def _read_ids_file(path: Path) -> list[int]:
    return _parse_ids_json(path.read_text(encoding="utf-8"))


async def _try_invalidate_redis_cache() -> bool:
    try:
        from redis.asyncio import Redis

        from bot.config.redis import RedisConfigClass

        redis_cfg = RedisConfigClass()
        client = Redis.from_url(redis_cfg.redis_url)
        await client.delete("kio:sponsors:active")
        async for key in client.scan_iter(match="kio:sponsor:member:*"):
            await client.delete(key)
        await client.aclose()
        return True
    except Exception:
        return False


async def list_sponsors() -> None:
    async with migration_session(dry_run=True) as session:
        result = await session.execute(select(AppSponser).order_by(AppSponser.id))
        sponsors = result.scalars().all()
        if not sponsors:
            print("No sponsors found in database.")
            return

        print(f"\n{'ID':<20} {'Status':<10} {'Name':<30} {'Link'}")
        print("-" * 80)
        for s in sponsors:
            status = "active" if s.is_active else "inactive"
            print(f"{s.id:<20} {status:<10} {s.name:<30} {s.link}")
        print("-" * 80)
        print(f"Total: {len(sponsors)} sponsor(s)\n")


async def remove_sponsors_async(
    target_ids: list[int] | None,
    *,
    remove_all: bool = False,
    soft: bool = False,
    dry_run: bool = False,
) -> None:
    action_name = "deactivated" if soft else "deleted"

    async with migration_session(dry_run=dry_run) as session:
        if remove_all:
            query = select(AppSponser)
            all_sponsors = (await session.execute(query)).scalars().all()
            if not all_sponsors:
                print("No sponsors found to remove.")
                return

            if soft:
                await session.execute(update(AppSponser).values(is_active=False))
            else:
                await session.execute(delete(AppSponser))

            print(f"{len(all_sponsors)} sponsor(s) {action_name}. dry_run={dry_run}")
        else:
            if not target_ids:
                print("No sponsor IDs specified.")
                return

            removed = 0
            not_found = 0

            for sp_id in target_ids:
                existing = (
                    await session.execute(select(AppSponser).where(AppSponser.id == sp_id))
                ).scalar_one_or_none()

                if existing is None:
                    print(f"  not found: {sp_id}")
                    not_found += 1
                    continue

                if soft:
                    existing.is_active = False
                else:
                    await session.delete(existing)

                removed += 1
                print(f"  - {sp_id} {existing.name} ({action_name})")

            print(f"\n{removed} {action_name}, {not_found} not found, dry_run={dry_run}")

    if not dry_run:
        invalidated = await _try_invalidate_redis_cache()
        if invalidated:
            print("Redis sponsor cache invalidated successfully.")
        else:
            print("Notice: Redis not reached. Run /update_sps in Telegram bot to refresh cache.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Remove or deactivate sponsor channels from database")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--id", type=int, nargs="+", help="One or more sponsor IDs to remove (e.g. --id -1001234567890)")
    group.add_argument("--json", help='JSON list of IDs or objects: [-100..., -100...] or [{"id": -100...}]')
    group.add_argument("--file", type=Path, help="Path to JSON file with sponsor IDs")
    group.add_argument("--all", action="store_true", help="Remove all sponsors")
    group.add_argument("--list", action="store_true", help="List all sponsors in database and exit")

    parser.add_argument("--soft", action="store_true", help="Deactivate (is_active=False) instead of deleting row")
    parser.add_argument("--dry-run", action="store_true", help="Preview without committing changes")

    args = parser.parse_args()

    if args.list:
        asyncio.run(list_sponsors())
        return

    if args.all:
        asyncio.run(remove_sponsors_async(None, remove_all=True, soft=args.soft, dry_run=args.dry_run))
        return

    if args.id:
        target_ids = list(args.id)
    elif args.json:
        target_ids = _parse_ids_json(args.json)
    elif args.file:
        target_ids = _read_ids_file(args.file)
    else:
        target_ids = []

    asyncio.run(remove_sponsors_async(target_ids, remove_all=False, soft=args.soft, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
