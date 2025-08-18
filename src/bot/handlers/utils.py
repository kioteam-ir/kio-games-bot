from ..gameUI import GameUI
from hydrogram import types
from core.game_engine.connect.with_friend import VsFriendEngine

def get_tg_keyboard(board,game:GameUI,game_id:int,game_over:bool) -> types.InlineKeyboardMarkup : 
    _ = []
    n = 1
    
    is_xo = game.is_xo
    current_player_id = game.current_player.id
    players = game.players
    _c = (game_over == False)
    
    for row in board :
        __ = []
        m=1
        for col in row :
            __.append(
                types.InlineKeyboardButton(
                    col.as_symbol if is_xo else col.as_color ,
                    f"cell_{n}_{m}_{game_id}" if _c else None,
                    None if _c else "https://t.me/kiogamesbot"

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
            f"player_info={players[0].id}"
        ),
        types.InlineKeyboardButton(
            f"🎮 {'' if _cond else '🔺'} {players[1].first_name}",
            f"player_info={players[1].id}"
        )
    ]
    _.append(_ps)
    return types.InlineKeyboardMarkup(_)

