from hydrogram import Client,types
from .game_utils import game_lists,GameTypes

from ..gameUI import GameUI
from services.game_session.session import session_manager
from services.local_texts.storage import texts_cache,CommandTypes
from core.game_engine.connect.with_friend import VsFriendEngine
from core.game_engine.XO.with_friend import VsFriendXO

from .utils import get_tg_keyboard, change_lang, is_joined, make_sponsors_keys
from .async_db import AsyncUserStats, AsyncGameModel

# -------------------------
# games list as inline keys
# -------------------------

async def gl_maker(lang_code:str,user_id:int) : 
    des = texts_cache.get(lang_code,CommandTypes.CHANGE_YOUR_LANG_TEXT)
    _ = [
        types.InlineQueryResultArticle(
            texts_cache.get(lang_code,CommandTypes.CHANGE_YOUR_LANG),
            types.InputTextMessageContent(des),
            999,
            None,
            des,
            types.InlineKeyboardMarkup([
                [types.InlineKeyboardButton("🇺🇸 English 🇺🇸",'chl_en')],
                [types.InlineKeyboardButton("🇮🇷 فارسی 🇮🇷",'chl_fa')],
                [types.InlineKeyboardButton("🇷🇺 Russian 🇷🇺",'chl_ru')],
            ])
        )
    ]

    games = [
        types.InlineQueryResultArticle(
                game_lists[lang_code][g].title,
                types.InputTextMessageContent(game_lists[lang_code][g].description + f"\n\n{texts_cache.get(lang_code,CommandTypes.CREATE_GAME_TEXT)}"),
                game_lists[lang_code][g]._id,
                thumb_url=game_lists[lang_code][g].thumb_url,
                description=game_lists[lang_code][g].description,
                reply_markup=await make_sponsors_keys([types.InlineKeyboardButton(texts_cache.get(lang_code,CommandTypes.CREATE_GAME_BUTTON),f'makegame_{user_id}_{game_lists[lang_code][g]._id}')])
            ) 
        for g in game_lists[lang_code]
    ]

    _.extend(games)
    return _


# --------------------
# choose result (game)
# --------------------

async def show_games(bot:Client,ir:types.InlineQuery) : 

    _user = await AsyncUserStats.get_or_create(ir.from_user.id,lang_code=ir.from_user.language_code if ir.from_user.language_code in texts_cache.langs else 'en')
    _l = _user['lang_code']
    if _user['is_banned'] : 
        await ir.answer(
            [
               types.InlineQueryResultArticle(
                texts_cache.get(_l,CommandTypes.YOU_ARE_BANNED_TITLE),
                types.InputTextMessageContent(texts_cache.get(_l,CommandTypes.YOU_ARE_BANNED_TEXT)),
                '-1',
                description=texts_cache.get(_l,CommandTypes.YOU_ARE_BANNED_TEXT)
            ) 
            ],0
        )
        return
    


    await ir.answer(await gl_maker(_l,ir.from_user.id),0)
    return



# ---------------------------
# cb handler
# ---------------------------
async def play_game(bot:Client,cb:types.CallbackQuery) :
    _user = await AsyncUserStats.get_or_create(cb.from_user.id,lang_code=cb.from_user.language_code if cb.from_user.language_code in texts_cache.langs else 'en') 
    _user_l = _user['lang_code'] 


    if cb.data.startswith("chl_") : 
        await change_lang(bot,cb)
        return


    if cb.data.startswith("playerinfo") : 
        _etc, player_id, game_type = cb.data.split("_")
        user_game_data: dict = await AsyncUserStats.retrieve_game(int(player_id),int(game_type))

        await cb.answer(
            texts_cache.get(_user_l,CommandTypes.PLAYER_GAME_STATS).format(
                all_games=user_game_data['total'],
                wins=user_game_data['wins'],
                losses=user_game_data['losses'],
                draws=user_game_data['draws']
            ),True
        )
        return


    clicked = cb.from_user.id
    mid = cb.inline_message_id

    _data_from_cb = cb.data.split("_") 
    gid = int(_data_from_cb[-1])

    if cb.data.startswith("makegame") :
        # only sender allowed to make game
        if clicked != (int(_data_from_cb[1])) : 
            await cb.answer("❌",True)
            return

        # check if user in sponsers
        if not await is_joined(bot,clicked) : 
            await cb.answer(texts_cache.get(_user_l,CommandTypes.JOIN_FIRST),True)
            return
        

        game_type_info = game_lists[_user_l][gid]
        
        _cond = (gid == GameTypes.XO)
        

        game = VsFriendXO(game_type_info.rows,game_type_info.connect) if _cond else VsFriendEngine(game_type_info.rows,game_type_info.cols,game_type_info.connect) 

        game_id = session_manager.push(
            GameUI(
                game,mid,cb.from_user,[cb.from_user],_cond, gid
            )
        )
        await bot.edit_inline_text(
            mid,
            f"{texts_cache.get(_user_l,CommandTypes.WAITING_FOR_PLAYER)}\n{game_type_info.description}",
            reply_markup=types.InlineKeyboardMarkup([[types.InlineKeyboardButton(texts_cache.get(_user_l,CommandTypes.IPLAY),f"iplay_{game_id}")]])
        )
        return

    game_info = session_manager.get(gid)

    game = game_info.game_engine
    players = game_info.players
    current_player = game_info.current_player


    if cb.data.startswith('iplay') : 
        # check if user in sponsers
        if not await is_joined(bot, clicked) : 
            await cb.answer(texts_cache.get(_user_l,CommandTypes.JOIN_FIRST),True)
            return
        

        if clicked in [player.id for player in players] : 
            await cb.answer(texts_cache.get(_user_l,CommandTypes.CANNOT_PLAY_WITH_YOURSELF),True)
            return
        
        await AsyncUserStats.get_or_create(cb.from_user.id,lang_code=cb.from_user.language_code if cb.from_user.language_code in texts_cache.langs else 'en')
        players.append(cb.from_user)

        # lang based on sender 
        game_lang = await AsyncUserStats.get_or_create(game_info.players[0].id)
        game_lang = game_lang['lang_code']
        await bot.edit_inline_text(
            mid,
            texts_cache.get(game_lang,CommandTypes.GAME_IN_PROGRESS_TEXT).format(
                name=current_player.first_name,
                color=game_info.game_engine.current_player.as_color
            ),
            reply_markup=get_tg_keyboard(game_info,gid,False)
        )


        return

    _c_r = cb.data.split("_")
    row = int(_c_r[1]) - 1 
    col = int(_c_r[2]) - 1

    if clicked not in [player.id for player in players] : 
        await cb.answer(texts_cache.get(_user_l,CommandTypes.NOT_YOUR_GAME),True)
        return

    if current_player.id != clicked : 
        await cb.answer(texts_cache.get(_user_l,CommandTypes.NOT_YOUR_TURN),True)
        return
    
    if not game.is_column_playable(col) : 
        await cb.answer(texts_cache.get(_user_l,CommandTypes.COLUMN_FULL),True)
        return



    game.make_move((row,col)) if game_info.is_xo else game.make_move(col)

    new_player = players[0] if current_player.id != players[0].id else players[1]
    game_info.current_player =  new_player


    _c = (game.ended or game.is_draw())


    # lang based on sender 
    game_lang = await AsyncUserStats.get_or_create(game_info.players[0].id)
    game_lang = game_lang['lang_code']

    text = ''
        # game ended 
    if _c : 

        _c_is_draw = (game.is_draw())

        # insert game to database
        players_info : dict = await AsyncGameModel.create(
            game_info.players[0].id,
            game_info.players[1].id,
            'draw' if _c_is_draw else f"player_{game_info.game_engine.winner.value}",
            game_info.game_type,
            mid
        )

        text = texts_cache.get(game_lang,CommandTypes.GAME_ENDED_TEXT).format(
            winner=texts_cache.get(game_lang,CommandTypes.GAME_IS_DRAW_TEXT) if _c_is_draw else game_info.players[game.winner.value - 1].first_name,
            total=players_info['total'],
            game=texts_cache.get(game_lang,CommandTypes.GAME),
            p1_name=game_info.players[0].first_name,
            p1_wins=players_info['p1_wins'],
            p2_name=game_info.players[1].first_name,
            p2_wins=players_info['p2_wins'],
            draws=players_info['draws']
        )
        
    else : 
        text = texts_cache.get(game_lang,CommandTypes.GAME_IN_PROGRESS_TEXT).format(
            name=new_player.first_name,
            color=game_info.game_engine.current_player.as_color
        )
    await bot.edit_inline_text(
        mid,                      
        text,
        reply_markup=get_tg_keyboard(game_info,gid,_c)
        )

    return