from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.infrastructure.database.connection import get_session_factory
from api.infrastructure.database.models import AppSponser
from bot.domain.repositories import SponsorRepository
from bot.domain.schemas.sponsor import SponsorRecord


class SqlAlchemySponsorRepository(SponsorRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession] | None = None) -> None:
        self._session_factory = session_factory or get_session_factory()

    async def list_active(self) -> list[SponsorRecord]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(AppSponser.id, AppSponser.name, AppSponser.link).where(AppSponser.is_active.is_(True))
            )
            rows = result.all()
            return [SponsorRecord(id=row.id, name=row.name, link=row.link) for row in rows]
