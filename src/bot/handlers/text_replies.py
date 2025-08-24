from hydrogram import Client,types,filters
from typing import Union

from .async_db import AsyncUserStats,TextModel
import asyncio

from services.local_texts.storage import texts_cache,CommandTypes
from .utils import is_joined, make_sponsors_keys

async def fast_reply(mes:types.Message,text,reply_markup:Union[types.ReplyKeyboardMarkup,types.InlineKeyboardMarkup,None]) -> types.Message : 
    _ = await mes.reply(
        text,True,
        reply_markup=reply_markup
    )
    return _


async def start_reply(mes:types.Message) -> types.Message :
    user_lang = mes.from_user.language_code if mes.from_user.language_code in texts_cache.langs else 'en'
    
    _user = await AsyncUserStats.get_or_create(mes.from_user.id,lang_code=user_lang)

    _ = await fast_reply(mes,texts_cache.get(_user['lang_code'],CommandTypes.START),reply_markup=None)
    return _

async def guide_reply(mes:types.Message) -> types.Message : 
    _ = await fast_reply(
        mes,
        "games list as keyboards for reading guide",
        types.ReplyKeyboardMarkup([['game_1','game_2']],resize_keyboard=True))
    return _












# ---------------
# static commands
# ---------------
_d= {
    '/start' : start_reply,
}
_dk = _d.keys()





async def welcome_handler(bot:Client,mes:types.Message) : 
    text = mes.text 
    user_lang = mes.from_user.language_code if mes.from_user.language_code in texts_cache.langs else 'en'
    
    _user = await AsyncUserStats.get_or_create(mes.from_user.id,lang_code=user_lang)

    if _user['is_banned'] : 
        await mes.reply(texts_cache.get(_user['lang_code'],CommandTypes.YOU_ARE_BANNED_TEXT),True)
        return

    if not is_joined(bot,mes.from_user.id) :        
        await mes.reply(texts_cache.get(_user['lang_code'],CommandTypes.JOIN_FIRST),True,reply_markup=make_sponsors_keys())
        return

    if text in _dk : 
        await _d[text](mes)
        return
