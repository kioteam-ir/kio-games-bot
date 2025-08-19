from typing import Union,List

from core.game_engine.connect.with_friend import VsFriendEngine
from core.game_engine.XO.with_friend import VsFriendXO
from hydrogram.types import User

class GameUI : 
    game_engine : Union[VsFriendXO,VsFriendEngine]
    inline_message_id : str
    current_player : User
    players : List[User]
    is_xo : bool
    game_type : int

    def __init__(
            self,
            game_engine : Union[VsFriendXO,VsFriendEngine], 
            inline_message_id : str, 
            current_player : User,
            players : List[User],
            is_xo: bool,
            game_type:int
        ):

        self.game_engine = game_engine
        self.inline_message_id = inline_message_id
        self.current_player = current_player
        self.players = players
        self.is_xo = is_xo
        self.game_type = game_type
        
