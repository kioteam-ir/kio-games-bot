from __future__ import annotations

import logging

from aiogram import Router
from aiogram.enums import ChatMemberStatus
from aiogram.types import ChatMemberUpdated

from bot.core.container import AppContainer

logger = logging.getLogger(__name__)

router = Router(name="sponsor")


@router.chat_member()
async def chat_member_update_handler(
    event: ChatMemberUpdated,
    container: AppContainer,
) -> None:
    if container.sponsor_checker is None:
        return

    sponsors = await container.sponsor_repo.list_active()
    sponsor_ids = {s.id for s in sponsors}
    if event.chat.id not in sponsor_ids:
        return

    target_user = event.new_chat_member.user
    new_status = event.new_chat_member.status

    if new_status in {ChatMemberStatus.LEFT, ChatMemberStatus.KICKED}:
        logger.info(
            "User %s left sponsor chat %s (status=%s). Invalidating membership cache.",
            target_user.id,
            event.chat.id,
            new_status,
        )
        await container.sponsor_checker.invalidate_user(target_user.id)
    else:
        logger.info(
            "User %s joined/updated in sponsor chat %s (status=%s). Updating membership status.",
            target_user.id,
            event.chat.id,
            new_status,
        )
        await container.sponsor_checker.invalidate_user(target_user.id)
        # Pre-cache if the user is now a member of all active sponsors
        await container.sponsor_checker.is_member_of_all(target_user.id, force_refresh=True)


@router.my_chat_member()
async def my_chat_member_update_handler(
    event: ChatMemberUpdated,
    container: AppContainer,
) -> None:
    if container.sponsor_checker is None:
        return

    sponsors = await container.sponsor_repo.list_active()
    sponsor_ids = {s.id for s in sponsors}
    if event.chat.id in sponsor_ids:
        logger.warning(
            "Bot status changed in sponsor chat %s to %s. Refreshing sponsors.",
            event.chat.id,
            event.new_chat_member.status,
        )
        await container.refresh_sponsors()

