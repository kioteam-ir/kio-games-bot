from hydrogram import Client
from .config import config


bot = Client(
    name=config.SESSION_NAME,
    bot_token=config.TOKEN,
    api_hash=config.API_HASH,
    api_id=config.API_ID
)
