from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.i18n import I18n

from bot.application.dto.game import SessionTimeoutResult
from bot.core.container import AppContainer
from bot.infrastructure.telegram.keyboards import KeyboardService
from bot.presentation.middlewares.container import ContainerMiddleware
from bot.presentation.middlewares.i18n import KioI18nMiddleware, UserLocaleMiddleware
from bot.presentation.middlewares.idempotency import CallbackIdempotencyMiddleware
from bot.presentation.middlewares.ratelimit import RateLimitMiddleware
from bot.presentation.middlewares.services import ServicesMiddleware
from bot.presentation.routers.fallback import catch_all_router, register_error_handler
from bot.presentation.routers.game import router as game_router
from bot.presentation.routers.start import router as start_router

logger = logging.getLogger(__name__)


class BotApplication:
    def __init__(self, container: AppContainer) -> None:
        self.container = container
        self.bot = Bot(
            token=container.bot_config.bot_token,
            default=DefaultBotProperties(parse_mode="HTML"),
        )
        self.dispatcher = Dispatcher(storage=MemoryStorage())
        self.root_router = Router(name="root")

    async def setup(self) -> None:
        self.container.bind_sponsor_checker(self.bot)
        await self.bot.delete_webhook(drop_pending_updates=True)
        self._register_session_timeout()
        self._register_middlewares()
        self._register_routers()

    async def start(self) -> None:
        await self.setup()
        await self.container.session_manager.rebuild_expiry_index()
        asyncio.create_task(self.container.session_manager.start_cleanup_loop())
        try:
            await self.dispatcher.start_polling(self.bot, polling_timeout=15)
        finally:
            await self.container.close()

    def _register_middlewares(self) -> None:
        i18n = I18n.get_current()
        if i18n is None:
            msg = "I18n is not initialized; import bot.i18n_bootstrap before BotApplication"
            raise RuntimeError(msg)

        self.dispatcher.update.middleware.register(ContainerMiddleware(self.container))
        self.dispatcher.update.middleware.register(
            UserLocaleMiddleware(self.container.user_service, self.container.i18n_config),
        )
        self.dispatcher.update.middleware.register(
            RateLimitMiddleware(self.container.rate_limit_service, self.container.rate_limit_config),
        )
        self.dispatcher.update.middleware.register(KioI18nMiddleware(i18n=i18n))
        self.dispatcher.update.middleware.register(ServicesMiddleware(self.container))
        self.dispatcher.callback_query.middleware.register(
            CallbackIdempotencyMiddleware(
                self.container.idempotency_store,
                ttl_seconds=int(self.container.session_config.callback_idempotency_ttl_seconds),
            ),
        )

    def _register_routers(self) -> None:
        register_error_handler(self.root_router)
        self.root_router.include_router(start_router)
        self.root_router.include_router(game_router)
        self.root_router.include_router(catch_all_router)
        self.dispatcher.include_router(self.root_router)

    def _register_session_timeout(self) -> None:
        async def on_session_deleted(game_id: int, session: object) -> None:
            from bot.domain.entities.game_session import GameSession

            if not isinstance(session, GameSession):
                return
            result = await self.container.game_flow_service.handle_timeout(game_id, session)
            if result is None:
                return
            await self._render_timeout(result)

        self.container.session_manager.subscribe("session_deleted", on_session_deleted)

    async def _render_timeout(self, result: SessionTimeoutResult) -> None:
        keyboards = KeyboardService(
            self.container.translator,
            self.container.bot_config.bot_username,
        )
        if result.board is None:
            markup = keyboards.timeout_keyboard(result.lang)
        else:
            from bot.application.dto.game import GameBoardView

            view = GameBoardView(
                text=result.text,
                game_id=result.game_id,
                game_over=True,
                board=result.board,
            )
            markup = keyboards.game_board(view)

        try:
            await self.bot.edit_message_text(
                inline_message_id=result.inline_message_id,
                text=result.text,
                reply_markup=markup,
            )
        except Exception:
            logger.exception(
                "Failed to edit inline message on session timeout game_id=%s inline_message_id=%s",
                result.game_id,
                result.inline_message_id,
            )
