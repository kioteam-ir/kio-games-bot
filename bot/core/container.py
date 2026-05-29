from __future__ import annotations

from dataclasses import dataclass

from aiogram import Bot
from aiogram.utils.i18n import I18n

from api.config.database import DatabaseConfigClass
from api.infrastructure.database.connection import init_database
from api.infrastructure.persistence.game_repository import SqlAlchemyGameRepository
from api.infrastructure.persistence.sponsor_repository import SqlAlchemySponsorRepository
from api.infrastructure.persistence.user_repository import SqlAlchemyUserRepository
from bot.application.services.game_catalog import GameCatalogService
from bot.application.services.game_flow import (
    ChangeLanguageService,
    GameFlowService,
    InlineGamesService,
    PlayerStatsService,
    UserService,
)
from bot.application.services.session_manager import (
    GameSessionManager,
    InMemoryGameSessionStorage,
)
from bot.config.bot import BotConfigClass
from bot.config.i18n import I18nConfigClass
from bot.config.session import SessionConfigClass
from bot.domain.repositories import (
    GameRepository,
    SponsorMembershipChecker,
    SponsorRepository,
    UserRepository,
)
from bot.infrastructure.i18n.translator import Translator
from bot.infrastructure.telegram.sponsor_checker import TelegramSponsorMembershipChecker


@dataclass(slots=True)
class AppContainer:
    bot_config: BotConfigClass
    session_config: SessionConfigClass
    i18n_config: I18nConfigClass
    translator: Translator
    catalog: GameCatalogService
    user_repo: UserRepository
    game_repo: GameRepository
    sponsor_repo: SponsorRepository
    session_manager: GameSessionManager
    user_service: UserService
    inline_games_service: InlineGamesService
    change_language_service: ChangeLanguageService
    player_stats_service: PlayerStatsService
    game_flow_service: GameFlowService
    sponsor_checker: SponsorMembershipChecker | None = None

    @classmethod
    def build(cls, bot_config: BotConfigClass | None = None) -> AppContainer:
        bot_cfg = bot_config or BotConfigClass()  # type: ignore[call-arg]
        session_cfg = SessionConfigClass()
        i18n_cfg = I18nConfigClass()
        i18n = I18n.get_current()
        translator = Translator(i18n_cfg, i18n)
        catalog = GameCatalogService()
        init_database(DatabaseConfigClass())
        user_repo = SqlAlchemyUserRepository()
        game_repo = SqlAlchemyGameRepository()
        sponsor_repo = SqlAlchemySponsorRepository()
        session_manager = GameSessionManager(
            storage=InMemoryGameSessionStorage(),
            timeout=session_cfg.game_session_timeout_seconds,
        )
        user_service = UserService(user_repo, translator)
        inline_games = InlineGamesService(user_service, catalog)
        change_lang = ChangeLanguageService(user_repo, translator)
        player_stats = PlayerStatsService(user_repo, translator)
        game_flow = GameFlowService(session_manager, catalog, game_repo, user_repo, translator)
        return cls(
            bot_config=bot_cfg,
            session_config=session_cfg,
            i18n_config=i18n_cfg,
            translator=translator,
            catalog=catalog,
            user_repo=user_repo,
            game_repo=game_repo,
            sponsor_repo=sponsor_repo,
            session_manager=session_manager,
            user_service=user_service,
            inline_games_service=inline_games,
            change_language_service=change_lang,
            player_stats_service=player_stats,
            game_flow_service=game_flow,
        )

    def bind_sponsor_checker(self, bot: Bot) -> None:
        self.sponsor_checker = TelegramSponsorMembershipChecker(bot, self.sponsor_repo)

    async def refresh_sponsors(self) -> int:
        sponsors = await self.sponsor_repo.list_active()
        return len(sponsors)
