from hydrogram import types, Client
from .async_db import AsyncTextModel


async def update_text_database(bot:Client,cb:types.CallbackQuery) : 
    if cb.data == 'update_texts' : 
        for lang in AsyncTextModel.get_langs() : 
            AsyncTextModel.get_text(lang) 
            

     