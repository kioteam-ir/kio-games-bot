from bot.bot import bot
from services.game_session.session import session_manager
from bot.handlers.on_delete import on_delete

async def main():
    session_manager._event_bus.subscribe('session_deleted',on_delete)
    await bot._client.start()
    await session_manager.start_cleanup_loop()

bot._client.run(main())
