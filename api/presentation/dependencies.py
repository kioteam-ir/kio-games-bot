from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from api.config.api import ApiConfig, ApiConfigClass
from api.infrastructure.database.connection import get_session_factory


def get_api_config() -> ApiConfigClass:
    return ApiConfig


async def get_session() -> AsyncIterator[AsyncSession]:
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
