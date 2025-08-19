from bot.bot import bot
from services.game_session.session import session_manager

async def main():
    await bot._client.start()
    await session_manager.start_cleanup_loop()

bot._client.run(main())
