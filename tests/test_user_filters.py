from __future__ import annotations

from datetime import UTC, datetime

import pytest

from bot.application.dto.game import ResolvedUserContext
from bot.domain.schemas.user import UserRecord
from bot.presentation.filters.user import BannedUserFilter, NotBannedFilter


def _context(*, banned: bool) -> ResolvedUserContext:
    user = UserRecord(
        id=1,
        is_banned=banned,
        is_superuser=False,
        lang_code="en",
        joined_time=datetime.now(tz=UTC),
        username="alice",
        name="Alice",
    )
    return ResolvedUserContext(user=user, lang="en")


@pytest.mark.asyncio
async def test_not_banned_filter_reads_user_context_from_kwargs() -> None:
    context = _context(banned=False)
    assert await NotBannedFilter()(**{"user_context": context}) == {}


@pytest.mark.asyncio
async def test_not_banned_filter_rejects_banned_user() -> None:
    context = _context(banned=True)
    assert await NotBannedFilter()(**{"user_context": context}) is False


@pytest.mark.asyncio
async def test_banned_filter_reads_user_context_from_kwargs() -> None:
    context = _context(banned=True)
    result = await BannedUserFilter()(**{"user_context": context})
    assert result == {"banned_context": context}
