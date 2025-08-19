from hydrogram import Client, filters, idle
from .config import Config
from typing import Any, Optional, Awaitable
from hydrogram.handlers.handler import Handler
from hydrogram.handlers import MessageHandler, CallbackQueryHandler, ChosenInlineResultHandler, InlineQueryHandler

from .handlers.inline_replies import *
from .handlers.text_replies import *

from services.game_session.session import session_manager



class Bot:
    def __init__(self, config: Config) -> None:
        # annotations
        self._client: Client
        
        # variables
        self.config = config
        
        # functions
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        config = self.config
        self._client = Client(
            name      = config.SESSION_NAME,
            bot_token = config.TOKEN,
            api_hash  = config.API_HASH,
            api_id    = config.API_ID,
        )
        
    def register_message_handler(self, func: Awaitable, /, *, 
                                 filters: Optional[filters.Filter] = None, 
                                 group: int = 0
                            ) -> None:
        message_handler = MessageHandler(func, filters)                 # pyright: ignore[reportArgumentType]
        self._add_handler(message_handler, group)
        
    def register_callbackquery_handler(self, func: Awaitable, /, *, 
                                       filters: Optional[filters.Filter] = None, 
                                       group: int = 0
                            ) -> None:
        callbackquery_handler = CallbackQueryHandler(func, filters)     # pyright: ignore[reportArgumentType]
        self._add_handler(callbackquery_handler, group)
        
    def _add_handler(self, handler: Handler, group: int = 0) -> None:
        self._client.add_handler(handler, group)
        
    async def run(self) -> None:
        await self._client.start()
        await session_manager.start_cleanup_loop()
        # await anti_spamm.start()
        pass


bot = Bot(config=Config.from_env())


bot.register_message_handler(welcome_handler)
bot._add_handler(InlineQueryHandler(show_games))
bot._add_handler(ChosenInlineResultHandler(send_game))
bot.register_callbackquery_handler(play_game)



__all__ = ("bot",)      # Only can import 'bot' name-space from this file