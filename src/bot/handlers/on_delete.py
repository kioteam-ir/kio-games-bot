from bot.gameUI import GameUI
from hydrogram import types,Client
from .utils import get_tg_keyboard  
from .async_db import AsyncGameModel,AsyncUserStats
from services.local_texts.storage import texts_cache, CommandTypes
from bot.bot import bot

bot = bot._client


async def on_delete(game_id:int, game_ui:GameUI) : 
        _user = await AsyncUserStats.get_or_create(game_ui.players[0].id)
        _user_l = _user['lang_code']
    # if game is multiplayer [future]


        # game has been started
        if len(game_ui.players) == 2 : 
            # if game has been ended before
            if game_ui.game_engine.ended : 
                return

            _c = 2 if game_ui.current_player == game_ui.players[0] else 1
            winner = game_ui.players[_c - 1]
            
            players_info = await AsyncGameModel.create(game_ui.players[0].id,game_ui.players[1].id,f"player_{_c}",game_ui.game_type,game_ui.inline_message_id)

            _help_text = texts_cache.get(_user_l,CommandTypes.GAME_ENDED_TEXT).format(
                winner=winner.first_name,
                total=players_info['total'],
                game=texts_cache.get(_user_l,CommandTypes.GAME),
                p1_name=game_ui.players[0].first_name,
                p1_wins=players_info['p1_wins'],
                p2_name=game_ui.players[1].first_name,
                p2_wins=players_info['p2_wins'],
                draws=players_info['draws']
            )
            text = f"""{texts_cache.get(_user_l,CommandTypes.GAME_STOPPED)}\n\n{_help_text}"""

            await bot.edit_inline_text(
                game_ui.inline_message_id,
                text,
                reply_markup=get_tg_keyboard(game_ui,game_id,True)
            )
            return

        # if game hasn't been started 
        if len(game_ui.players) == 1 :
            text = texts_cache.get(_user_l,CommandTypes.PLAY_WITH_COOL_PEOPLE_TEXT)
            await bot.edit_inline_text(
                game_ui.inline_message_id,
                text,
                reply_markup=types.InlineKeyboardMarkup(
                     [[types.InlineKeyboardButton(texts_cache.get(_user_l,CommandTypes.PLAY_WITH_COOL_PEOPLE_BUTTON),switch_inline_query=" ")]]
                )
            )
            return
