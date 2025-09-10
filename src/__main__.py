from bot.bot import bot
from services.game_session.session import session_manager
from bot.handlers.on_delete import on_delete
import sys
from bot.logger import setup_logger

logger = setup_logger()

def custom_excepthook(exc_type, exc_value, exc_traceback):
    logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
    sys.exit(1)

sys.excepthook = custom_excepthook
sys.stdout = open('stdout.log', 'a')
sys.stderr = open('stderr.log', 'a')

async def main():
    session_manager._event_bus.subscribe('session_deleted',on_delete)
    await bot._client.start()
    await session_manager.start_cleanup_loop()

bot._client.run(main())