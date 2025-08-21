from bot.gameUI import GameUI
from hydrogram import types,Client
from .utils import get_tg_keyboard  
from .async_db import AsyncGameModel
from bot.bot import bot


async def on_delete(game_id:int, game:GameUI, bot:Client) : 
    # if game is multiplayer [future]


        # game has been started
        if len(game.players) == 2 : 
            _c = 2 if game.current_player == game.players[0] else 1
            winner = game.players[_c - 1]
            
            players_info = AsyncGameModel.create(game.players[0].id,game.players[1].id,f"player_{_c}",game.game_type,game.inline_message_id)

            text = f"""🎮 بازی به دلیل وقفه زیاد، متوقف شد 🎮

🏆برنده بازی :  {winner.first_name} 
⚔نتایج کل مسابقات بین شما دونفر:  [{players_info['total']} بازی]
1️⃣ {game.players[0].first_name} : {players_info['p1_wins']}
2️⃣ {game.players[1].first_name} : {players_info['p2_wins']}
🟰 تساوی ها : {players_info['draws']}"""

            await bot.edit_inline_text(
                game.inline_message_id,
                text,
                reply_markup=get_tg_keyboard(game,game_id,True)
            )

        # if game hasn't been started 
        if len(game.players == 1) :
            text = '😬🎮 هیچکسی مایل به بازی کردن نبود 😬\n\nپیش آدم باحالا بفرست اینا که نمیان بازی 😒'
            await bot.edit_inline_text(
                game.inline_message_id,
                text,
                reply_markup=types.InlineKeyboardMarkup(
                     [[types.InlineKeyboardButton("😎 بازی با آدم باحالا 😎",switch_inline_query=" ")]]
                )
            )
            return
