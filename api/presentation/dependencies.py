from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from api.config.api import ApiConfig, ApiConfigClass
from api.infrastructure.database.connection import get_session_factory
from bot.application.services.game_flow import GameFlowService
from bot.application.services.session_manager import GameSessionManager
from bot.core.container import AppContainer


async def get_session() -> AsyncIterator[AsyncSession]:
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_api_config() -> ApiConfigClass:
    return ApiConfig


def get_container(request: Request) -> AppContainer:
    container = getattr(request.app.state, "container", None)
    if container is None:
        msg = "Application container is not initialized"
        raise RuntimeError(msg)
    if not isinstance(container, AppContainer):
        msg = "Invalid application container type"
        raise TypeError(msg)
    return container


ContainerDep = Annotated[AppContainer, Depends(get_container)]


def get_game_flow_service(container: ContainerDep) -> GameFlowService:
    return container.game_flow_service


def get_session_manager(container: ContainerDep) -> GameSessionManager:
    return container.session_manager


GameFlowDep = Annotated[GameFlowService, Depends(get_game_flow_service)]
SessionManagerDep = Annotated[GameSessionManager, Depends(get_session_manager)]
