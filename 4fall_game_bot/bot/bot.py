from hydrogram import Client
from .config import config


bot = Client(
    # Session name
    name = config.SESSION_NAME,
    
    # Bot Token
    bot_token = config.TOKEN,
    
    # API
    api_hash = config.API_HASH or None,
    api_id   = config.API_ID   or None,
)

__all__ = ("bot",)      # Only can import 'bot' name-space from this file