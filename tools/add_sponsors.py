#!/usr/bin/env python3
"""Add sponsor channels to the database."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from pydantic import TypeAdapter
from sqlalchemy import select

from api.infrastructure.database.models import AppSponser
from tools.common import migration_session
from tools.schemas import SponsorInput

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

SponsorList = TypeAdapter(list[SponsorInput])


def _parse_sponsors_json(raw: str) -> list[SponsorInput]:
    payload = json.loads(raw)
    return SponsorList.validate_python(payload)


def _read_sponsors_file(path: Path) -> list[SponsorInput]:
    return _parse_sponsors_json(path.read_text(encoding="utf-8"))


async def main_async(sponsors: list[SponsorInput], *, dry_run: bool) -> None:
    if not sponsors:
        print("No sponsors to add.")
        return

    added = 0
    skipped = 0

    async with migration_session(dry_run=dry_run) as session:
        for sponsor in sponsors:
            existing = (
                await session.execute(select(AppSponser).where(AppSponser.id == sponsor.id))
            ).scalar_one_or_none()
            if existing is not None:
                print(f"  skip (exists): {sponsor.id} {sponsor.name}")
                skipped += 1
                continue

            session.add(
                AppSponser(
                    id=sponsor.id,
                    name=sponsor.name,
                    link=sponsor.link,
                    joined_memebers=sponsor.joined_memebers,
                    is_active=sponsor.is_active,
                )
            )
            added += 1
            print(f"  + {sponsor.id} {sponsor.name}")

    print(f"\nAdded {added}, skipped {skipped}, dry_run={dry_run}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Add sponsor channels to app_sponser")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--json", help='JSON list: [{"id":-100..., "name":"...", "link":"..."}]')
    group.add_argument("--file", type=Path, help="Path to JSON file with sponsor list")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    sponsors = _parse_sponsors_json(args.json) if args.json else _read_sponsors_file(args.file)
    asyncio.run(main_async(sponsors, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
