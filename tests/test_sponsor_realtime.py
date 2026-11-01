from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.enums import ChatMemberStatus
from aiogram.types import Chat, ChatMemberLeft, ChatMemberMember, ChatMemberUpdated, User

from bot.domain.schemas.sponsor import SponsorRecord
from bot.infrastructure.cache.redis_cache import InMemoryCacheBackend
from bot.infrastructure.telegram.sponsor_checker import TelegramSponsorMembershipChecker
from bot.presentation.routers.sponsor import chat_member_update_handler, my_chat_member_update_handler


def _create_chat_member_event(
    chat_id: int,
    user_id: int,
    status: ChatMemberStatus,
) -> ChatMemberUpdated:
    user = User(id=user_id, is_bot=False, first_name="TestUser")
    chat = Chat(id=chat_id, type="channel", title="Sponsor Channel")
    if status == ChatMemberStatus.LEFT:
        new_cm = ChatMemberLeft(user=user)
    else:
        new_cm = ChatMemberMember(user=user)
    old_cm = ChatMemberMember(user=user)
    return ChatMemberUpdated(
        chat=chat,
        from_user=user,
        date=123456789,
        old_chat_member=old_cm,
        new_chat_member=new_cm,
    )


@pytest.mark.asyncio
async def test_chat_member_left_invalidates_cache() -> None:
    container = MagicMock()
    sponsor_repo = AsyncMock()
    sponsor_repo.list_active.return_value = [
        SponsorRecord(id=-1001, name="Sp1", link="https://t.me/sp1", joined_memebers=0, is_active=True),
    ]
    sponsor_checker = AsyncMock()
    container.sponsor_repo = sponsor_repo
    container.sponsor_checker = sponsor_checker

    event = _create_chat_member_event(chat_id=-1001, user_id=42, status=ChatMemberStatus.LEFT)
    await chat_member_update_handler(event, container)

    sponsor_checker.invalidate_user.assert_awaited_once_with(42)
    sponsor_checker.is_member_of_all.assert_not_called()


@pytest.mark.asyncio
async def test_chat_member_joined_warms_cache() -> None:
    container = MagicMock()
    sponsor_repo = AsyncMock()
    sponsor_repo.list_active.return_value = [
        SponsorRecord(id=-1001, name="Sp1", link="https://t.me/sp1", joined_memebers=0, is_active=True),
    ]
    sponsor_checker = AsyncMock()
    container.sponsor_repo = sponsor_repo
    container.sponsor_checker = sponsor_checker

    event = _create_chat_member_event(chat_id=-1001, user_id=42, status=ChatMemberStatus.MEMBER)
    await chat_member_update_handler(event, container)

    sponsor_checker.invalidate_user.assert_awaited_once_with(42)
    sponsor_checker.is_member_of_all.assert_awaited_once_with(42, force_refresh=True)


@pytest.mark.asyncio
async def test_chat_member_ignored_for_non_sponsor() -> None:
    container = MagicMock()
    sponsor_repo = AsyncMock()
    sponsor_repo.list_active.return_value = [
        SponsorRecord(id=-1001, name="Sp1", link="https://t.me/sp1", joined_memebers=0, is_active=True),
    ]
    sponsor_checker = AsyncMock()
    container.sponsor_repo = sponsor_repo
    container.sponsor_checker = sponsor_checker

    event = _create_chat_member_event(chat_id=-9999, user_id=42, status=ChatMemberStatus.LEFT)
    await chat_member_update_handler(event, container)

    sponsor_checker.invalidate_user.assert_not_called()


@pytest.mark.asyncio
async def test_my_chat_member_refreshes_sponsors() -> None:
    container = MagicMock()
    sponsor_repo = AsyncMock()
    sponsor_repo.list_active.return_value = [
        SponsorRecord(id=-1001, name="Sp1", link="https://t.me/sp1", joined_memebers=0, is_active=True),
    ]
    container.sponsor_repo = sponsor_repo
    container.refresh_sponsors = AsyncMock()

    event = _create_chat_member_event(chat_id=-1001, user_id=999, status=ChatMemberStatus.LEFT)
    await my_chat_member_update_handler(event, container)

    container.refresh_sponsors.assert_awaited_once()


@pytest.mark.asyncio
async def test_sponsor_membership_checker_immediate_invalidation() -> None:
    bot = AsyncMock()
    cache = InMemoryCacheBackend()
    sponsor_repo = AsyncMock()
    sponsor_repo.list_active.return_value = [
        SponsorRecord(id=-1001, name="Sp1", link="https://t.me/sp1", joined_memebers=0, is_active=True),
    ]

    checker = TelegramSponsorMembershipChecker(
        bot,
        sponsor_repo,
        cache=cache,
        membership_ttl_seconds=30,
    )

    # First check: bot says member
    bot.get_chat_member.return_value = MagicMock(status=ChatMemberStatus.MEMBER)
    assert await checker.is_member_of_all(42) is True
    assert bot.get_chat_member.call_count == 1

    # Second check hits cache, no bot call
    assert await checker.is_member_of_all(42) is True
    assert bot.get_chat_member.call_count == 1

    # User leaves: invalidate user
    await checker.invalidate_user(42)

    # Now bot says left
    bot.get_chat_member.return_value = MagicMock(status=ChatMemberStatus.LEFT)
    assert await checker.is_member_of_all(42) is False
    assert bot.get_chat_member.call_count == 2



@pytest.mark.asyncio
async def test_adding_sponsor_invalidates_previous_member_cache() -> None:
    bot = AsyncMock()
    cache = InMemoryCacheBackend()
    sponsor_repo = AsyncMock()
    sponsor_repo.list_active.return_value = [
        SponsorRecord(id=-1001, name="Sp1", link="https://t.me/sp1", joined_memebers=0, is_active=True),
    ]

    checker = TelegramSponsorMembershipChecker(
        bot,
        sponsor_repo,
        cache=cache,
        membership_ttl_seconds=30,
    )

    bot.get_chat_member.return_value = MagicMock(status=ChatMemberStatus.MEMBER)
    assert await checker.is_member_of_all(42) is True
    assert bot.get_chat_member.call_count == 1

    # Sponsor 2 is added
    sponsor_repo.list_active.return_value = [
        SponsorRecord(id=-1001, name="Sp1", link="https://t.me/sp1", joined_memebers=0, is_active=True),
        SponsorRecord(id=-1002, name="Sp2", link="https://t.me/sp2", joined_memebers=0, is_active=True),
    ]

    async def mock_get_chat_member(chat_id: int, user_id: int):
        if chat_id == -1001:
            return MagicMock(status=ChatMemberStatus.MEMBER)
        return MagicMock(status=ChatMemberStatus.LEFT)

    bot.get_chat_member.side_effect = mock_get_chat_member
    assert await checker.is_member_of_all(42) is False
