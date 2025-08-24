from hydrogram import types, Client
from services.sponsers.storage import sponsor_cache
admins = []
async def update_cache(bot:Client, mes:types.Message) : 
    if not mes.from_user.id in admins : 
        return
    
    if mes.text and mes.text == '/update_sps' : 
        sponsor_cache.update_all()
        await mes.reply("sposnors updated :)",True)
        return