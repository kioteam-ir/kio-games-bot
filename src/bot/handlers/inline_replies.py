from hydrogram import Client,types
from .game_utils import game_lists,GameTypes

from ..gameUI import GameUI
from services.game_session.session import session_manager
from core.game_engine.connect.with_friend import VsFriendEngine
from core.game_engine.XO.with_friend import VsFriendXO

from .utils import get_tg_keyboard
from .async_db import AsyncUserStats, AsyncGameModel


# -------------------------
# games list as inline keys
# -------------------------
_gl = [
    types.InlineQueryResultArticle(
            game_lists[g].title,
            types.InputTextMessageContent(game_lists[g].description + "\n\n🕹 اوکیه؟ پس بزن ساخت بازی 🕹"),
            game_lists[g]._id,
            thumb_url=game_lists[g].thumb_url,
            description=game_lists[g].description,
            reply_markup=types.InlineKeyboardMarkup([[types.InlineKeyboardButton("🕹 ساخت بازی 🕹",f'makegame_{game_lists[g]._id}')]])
        ) 
    for g in game_lists
]


# --------------------
# choose result (game)
# --------------------

async def show_games(bot:Client,ir:types.InlineQuery) : 

    _user = await AsyncUserStats.get_or_create(ir.from_user.id)
    if _user['is_banned'] : 
        await ir.answer(
            [
               types.InlineQueryResultArticle(
                "you are banned",
                types.InputTextMessageContent(""),
                '-1',
                description="you have been banned from using this robot"
            ) 
            ],0
        )
        return
    


    await ir.answer(_gl,0)
    return



# ---------------------------
# cb handler
# ---------------------------
async def play_game(bot:Client,cb:types.CallbackQuery) : 

    if cb.data.startswith("playerinfo") : 
        _etc, player_id, game_type = cb.data.split("_")
        user_game_data: dict = await AsyncUserStats.retrieve_game(int(player_id),int(game_type))

        await cb.answer(
            f"""
📊 اطلاعات بازی کاربر 📊

🕹همه بازی ها [{user_game_data['total']}]🕹
🥇برد ها [{user_game_data['wins']}] 🥇
🥈باخت ها [{user_game_data['losses']}] 🥈
🟰 تساوی ها [{user_game_data['draws']}] 🟰

"""         ,True
        )
        return


    clicked = cb.from_user.id
    mid = cb.inline_message_id

    gid = int(cb.data.split("_")[-1])

    if cb.data.startswith("makegame") :
        game_type = gid
        game_type_info = game_lists[game_type]
        
        _cond = (game_type == GameTypes.XO)
        

        game = VsFriendXO(game_type_info.rows,game_type_info.connect) if _cond else VsFriendEngine(game_type_info.rows,game_type_info.cols,game_type_info.connect) 

        game_id = session_manager.push(
            GameUI(
                game,mid,cb.from_user,[cb.from_user],_cond, game_type
            )
        )

        await bot.edit_inline_text(
            mid,
            f"⏳ در انتظار بازیکن... ⏳\n{game_type_info.description}",
            reply_markup=types.InlineKeyboardMarkup([[types.InlineKeyboardButton('بازی میکنم 🙋',f"iplay_{game_id}")]])
        )
        return

    game_info = session_manager.get(gid)

    game = game_info.game_engine
    players = game_info.players
    current_player = game_info.current_player


    if cb.data.startswith('iplay') : 
        if clicked in [player.id for player in players] : 
            await cb.answer("نمیتوانید با خودتان بازی کنید 😅",True)
            return
        
        await AsyncUserStats.get_or_create(cb.from_user.id)
        players.append(cb.from_user)
        await bot.edit_inline_text(
            mid,
            f"🕹 نوبت : {current_player.first_name} [{game_info.game_engine.current_player.as_color}]\t\t\tㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤ\n🕹 بازی کنید 🕹",                               
            reply_markup=get_tg_keyboard(game_info,gid,False)
        )


        return

    _c_r = cb.data.split("_")
    row = int(_c_r[1]) - 1 
    col = int(_c_r[2]) - 1

    if clicked not in [player.id for player in players] : 
        await cb.answer("❌ شما در این بازی نیستید ❌",True)
        return

    if current_player.id != clicked : 
        await cb.answer("❌ نوبت شما نیست ❌",True)
        return
    
    if not game.is_column_playable(col) : 
        await cb.answer("❌ ستون پر شده است ❌",True)
        return



    game.make_move((row,col)) if game_info.is_xo else game.make_move(col)

    new_player = players[0] if current_player.id != players[0].id else players[1]
    game_info.current_player =  new_player


    _c = (game.ended or game.is_draw())

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

        text = f"""🏆برنده بازی : {'بدون برنده 💢' if _c_is_draw else game_info.players[game.winner.value - 1].first_name } 
⚔نتایج کل مسابقات بین شما دونفر:  [{players_info['total']} بازی]
1️⃣ {game_info.players[0].first_name} : {players_info['p1_wins']}
2️⃣ {game_info.players[1].first_name} : {players_info['p2_wins']}
🟰 تساوی ها : {players_info['draws']}
"""
    else : 
        text = f"🕹 نوبت : {new_player.first_name} [{game_info.game_engine.current_player.as_color}]\t\t\tㅤㅤㅤㅤㅤㅤㅤㅤ\n🕹 بازی کنید 🕹" 


    await bot.edit_inline_text(
        mid,                      
        text,
        reply_markup=get_tg_keyboard(game_info,gid,_c)
        )

    return