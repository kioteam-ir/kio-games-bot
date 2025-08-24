from ..gameUI import GameUI
from hydrogram import types, Client
from core.game_engine.connect.with_friend import VsFriendEngine
from services.local_texts.storage import texts_cache,CommandTypes
from async_db import UserStats
from services.sponsers.storage import sponsor_cache

def get_tg_keyboard(game:GameUI,game_id:int,game_over:bool) -> types.InlineKeyboardMarkup : 
    _ = []
    n = 1
    
    is_xo = game.is_xo
    current_player_id = game.current_player.id
    players = game.players
    _c = (game_over == False)
    
    for row in game.game_engine.board :
        __ = []
        m=1
        for col in row :
            __.append(
                types.InlineKeyboardButton(
                    col.as_symbol if is_xo else col.as_color ,
                    f"cell_{n}_{m}_{game_id}" if _c else None,
                    None if _c else "https://t.me/kiogamesbot",

                )
            )
            m+=1
        _.append(__)
        n+=1
    
    if isinstance(game.game_engine,VsFriendEngine) : 
        _lm = []
        legal_moves = game.game_engine.legal_moves()
        for j in range(0,game.game_engine.cols) :
            t = ''
            if j not in legal_moves : 
                t = '🚫'
            else : 
                t = '✅'

            _lm.append(
                types.InlineKeyboardButton(
                    t,f"cell_0_{j+1}_{game_id}" if _c else None, None if _c else "https://t.me/kiogamesbot"
                )
            )

        _.append(_lm)

    _cond = current_player_id==players[0].id
    
    _ps = [
        types.InlineKeyboardButton(
            f"🎮 {'🔺' if _cond else ''} {players[0].first_name}",
            f"playerinfo_{players[0].id}_{game.game_type}"
        ),
        types.InlineKeyboardButton(
            f"🎮 {'' if _cond else '🔺'} {players[1].first_name}",
            f"playerinfo_{players[1].id}_{game.game_type}"
        )
    ]
    _.append(_ps)
    return types.InlineKeyboardMarkup(_)

async def change_lang(bot:Client,cb:types.CallbackQuery) : 
    new_l = cb.data.split("_")[-1]
    u = cb.from_user.id
    if new_l not in texts_cache.langs :
        await UserStats.change_lang(u,"en")
    else : 
        await UserStats.change_lang(u,new_l)

    await cb.answer(
        texts_cache.get(new_l,CommandTypes.LANG_CHANGED),True
    )
    return


async def is_joined(bot:Client,user_id:int) -> bool : 
    sps = sponsor_cache.get_all()
    for sp in sps : 
        try : 
            await bot.get_chat_member(sp.link, user_id)
        except : 
            return False
    return True


def make_sponsors_keys(extra_key:list=[], index:int=0) -> types.InlineKeyboardMarkup : 
    _ = [
        [types.InlineKeyboardButton(sp.name,url=sp.link)] for sp in sponsor_cache.get_all()
    ]
    if extra_key :
        _.insert(
            index,
            extra_key
        )
    
    return types.InlineKeyboardMarkup(_)