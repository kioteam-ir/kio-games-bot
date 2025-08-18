from hydrogram import Client,types,filters
from typing import Union

from db.orm import UserStats





async def fast_reply(mes:types.Message,text,reply_markup:Union[types.ReplyKeyboardMarkup,types.InlineKeyboardMarkup,None]) -> types.Message : 
    _ = await mes.reply(
        text,True,
        reply_markup=reply_markup
    )
    return _


async def start_reply(mes:types.Message) -> types.Message : 
    _ = await fast_reply(mes,"start text",reply_markup=None)
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
    'games guide' : guide_reply,
}
_dk = _d.keys()





async def welcome_handler(bot:Client,mes:types.Message) : 
    text = mes.text 
    user_lang = mes.from_user.language_code

    _user = UserStats.get_or_create(mes.from_user.id)

    if _user['is_banned'] : 
        await mes.reply("you have been banned from using this robot.",True)
        return

    if text in _dk : 
        await _d[text](mes)
        return

    if text.startswith("game") : 
        gid = int(text.split("_")[-1])
        text = 'game [name] guid :\n\nhello'
        await mes.reply(text,True,reply_markup=types.ReplyKeyboardMarkup([['game_1','game_2']],resize_keyboard=True))
        return
    