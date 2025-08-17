import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from app.models import User, Game, LocalizedText


class UserStats:

    @staticmethod
    def get_or_create(id: int, is_superuser: bool = False, is_banned: bool = False, lang_code: str = "fa") -> dict:
        return User.get_or_create(id, is_superuser, is_banned, lang_code)


    @staticmethod
    def get_all(id: int) -> dict:
        return User.all_data(id)
    

    @staticmethod
    def toggle_ban(user_id: int, is_banned: bool) -> None:
        return User.status(user_id, is_banned)
    

class GameModel:

    @staticmethod
    def create(player_1: int, player_2: int, result: str, type: int, mid: str) -> None:
        Game.geme_add(player_1, player_2, type, result, mid)
        

class TextModel:

    @staticmethod
    def get_text(lang_code: str = "fa") -> list:
        return LocalizedText.get_text(lang_code)