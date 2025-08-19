from orm import GameModel, UserStats
from asgiref.sync import sync_to_async



class AsyncUserStats:
    def __init__(self, user_stats):
        self.user_stats = user_stats

        for attr_name in dir(self.user_stats):
            if not attr_name.startswith("_"):
                attr = getattr(self.user_stats, attr_name)
                if callable(attr):
                    setattr(self, attr_name, sync_to_async(attr))


AsyncUserStats:UserStats = AsyncUserStats(UserStats)