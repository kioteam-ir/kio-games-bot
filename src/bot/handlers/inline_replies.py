from hydrogram import Client,types,filters
from typing import Union
from .game_utils import game_lists,EachGame,GameTypes

# --------------------
# choose result (game)
# --------------------
async def show_games(bot:Client,ir:types.InlineQuery) : 
    _ = []
    for g in game_lists : 
        g : EachGame = game_lists[g]
        _.append(
            types.InlineQueryResultArticle(
                g.title,
                types.InputTextMessageContent(g.message_text),
                g._id,
                thumb_url=g.thumb_url,
                description=g.description,
                reply_markup=types.InlineKeyboardMarkup([[types.InlineKeyboardButton("loading ...",'bluh')]])
            )
        )

    await ir.answer(_)
    return



# ---------------------------
# temp game-manager
# ---------------------------
from core.game_engine.with_friend import VsFriendEngine
dic = {
    # "inline mid" : {
    #     "mid" : "mid",
    #     "game" : VsFriendEngine
    # } 

}



def get_tg_keyboard(board,players) -> types.InlineKeyboardMarkup : 
    _ = []
    n = 1
    for row in board :
        __ = []
        m=1
        for col in row :
            __.append(
                types.InlineKeyboardButton(
                    "⬜️" if col.is_empty else ("🔵" if col == 1 else '🔴'),
                    f"cell[{n},{m}]"
                )
            )
            m+=1
        _.append(__)
        n+=1
    _ps = []
    for player in players : 
        _ps.append(types.InlineKeyboardButton(
                    f"p : {player}",
                    f"player_info={player}"
                )) 
    _.append(_ps)
    return types.InlineKeyboardMarkup(_)


# ---------------------------
# chosen inline result (game)
# ---------------------------

async def send_game(bot:Client,cir:types.ChosenInlineResult) : 
    mid = cir.inline_message_id
    game_id = int(cir.result_id)

    chosen_game = game_lists[game_id]

    
    #connect 4
    rows = 6
    cols = 7
    connect = 4
    
    if game_id == GameTypes.XO : 
        rows = 3 
        cols = 3
        connect = 3
    if game_id == GameTypes.C3 : 
        connect = 3
    
    # if game_id == GameTypes.C4 : pass 
    if game_id == GameTypes.C5 : 
        rows = 7
        cols = 8
        connect = 5

    game = VsFriendEngine(rows,cols,connect)
    
    dic[mid] = {
        "mid" : mid,
        "game" : game,
        "players" : [cir.from_user.id],
        "current_player" :cir.from_user.id
    }

    await bot.edit_inline_text(
        mid,
        f"در انتظار بازیکن...",
        reply_markup=types.InlineKeyboardMarkup([[types.InlineKeyboardButton('بازی میکنم',"iplay")]])
    )
    return


# ---------------------------
# cb handler
# ---------------------------
async def play_game(bot:Client,cb:types.CallbackQuery) : 
    clicked = cb.from_user.id
    mid = cb.inline_message_id

    game:VsFriendEngine = dic[mid]['game']
    players = dic[mid]['players']

    if cb.data == 'iplay' : 
        if clicked in players : 
            await cb.answer("وایسا بچه سال")
            return
        
        dic[mid]['players'].append(clicked)
        await bot.edit_inline_text(mid,
                               
        f"نوبت : {dic[mid]['current_player']}                          ‌\nبازی کنید",
                               
                               reply_markup=get_tg_keyboard(game.board,dic[mid]['players']))


        return


    col = int(cb.data.replace("cell","").replace("[","").replace("]","").split(",")[-1]) - 1
    

    current_player = dic[mid]['current_player']

    if clicked not in players : 
        await cb.answer("شما در این بازی نیستید")
        return

    if current_player != clicked : 
        await cb.answer("نوبت شما نیست")
        return
    
    if game.ended : 
        await cb.answer("بازی تمام شده است.")
        return
    
    if game.is_draw() : 
        await cb.answer("بازی مساوی شد")
        return



    game.make_move(col)

    player = dic[mid]['players']
    new_player = player[0] if current_player != player[0] else player[1]
    dic[mid]['current_player'] =  new_player

    await bot.edit_inline_text(mid,
                               
        f"نوبت : {new_player}                          ‌\nبازی کنید",
                               
                               reply_markup=get_tg_keyboard(game.board,player))

    return