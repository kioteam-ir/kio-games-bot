from orm import GameModel, UserStats, SponserModel
from asgiref.sync import sync_to_async



class AsyncUserStats:
    def __init__(self, user_stats):
        self.user_stats = user_stats

        for attr_name in dir(self.user_stats):
            if not attr_name.startswith("_"):
                attr = getattr(self.user_stats, attr_name)
                if callable(attr):
                    setattr(self, attr_name, sync_to_async(attr))

class AsyncGameModel : 
    def __init__(self,game_model):
        self.game_model = game_model


        for attr_name in dir(self.game_model):
            if not attr_name.startswith("_"):
                attr = getattr(self.game_model, attr_name)
                if callable(attr):
                    setattr(self, attr_name, sync_to_async(attr))


class AsyncSponserModel : 
    def __init__(self,text_model):
        self.text_model = text_model


        for attr_name in dir(self.text_model):
            if not attr_name.startswith("_"):
                attr = getattr(self.text_model, attr_name)
                if callable(attr):
                    setattr(self, attr_name, sync_to_async(attr))

AsyncUserStats:UserStats = AsyncUserStats(UserStats)
AsyncGameModel:GameModel = AsyncGameModel(GameModel)
AsyncSponserModel:SponserModel = AsyncSponserModel(SponserModel)