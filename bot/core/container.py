from __future__ import annotations

from dataclasses import dataclass

from aiogram import Bot

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
from api.config.database import DatabaseConfigClass
from api.infrastructure.database.connection import init_database
from api.infrastructure.persistence.game_repository import SqlAlchemyGameRepository
from api.infrastructure.persistence.sponsor_repository import SqlAlchemySponsorRepository
from api.infrastructure.persistence.user_repository import SqlAlchemyUserRepository
from bot.infrastructure.i18n.texts import TextsService
from bot.infrastructure.telegram.sponsor_checker import TelegramSponsorMembershipChecker


@dataclass(slots=True)
class AppContainer:
    bot_config: BotConfigClass
    session_config: SessionConfigClass
    texts: TextsService
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
        texts = TextsService(i18n_cfg)
        catalog = GameCatalogService()
        init_database(DatabaseConfigClass())
        user_repo = SqlAlchemyUserRepository()
        game_repo = SqlAlchemyGameRepository()
        sponsor_repo = SqlAlchemySponsorRepository()
        session_manager = GameSessionManager(
            storage=InMemoryGameSessionStorage(),
            timeout=session_cfg.game_session_timeout_seconds,
        )
        user_service = UserService(user_repo, texts)
        inline_games = InlineGamesService(user_service, catalog)
        change_lang = ChangeLanguageService(user_repo, texts)
        player_stats = PlayerStatsService(user_repo, texts)
        game_flow = GameFlowService(session_manager, catalog, game_repo, user_repo, texts)
        return cls(
            bot_config=bot_cfg,
            session_config=session_cfg,
            texts=texts,
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
