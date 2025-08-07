from hydrogram import Client, types, enums, errors
from config import Api,TOKEN

bot = Client('fallgame',Api.ID,Api.HASH,bot_token=TOKEN)



@bot.on_inline_query()
async def show_games(bot:Client,cb:types.InlineQuery) : 
    ...


bot.run()