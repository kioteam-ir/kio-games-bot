"""
Usage: from db.orm import UserStats, GameModel, TextModel.
"""


import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from app.models import *


class UserStats:
    """
    This model is for working with user data.
    P.S: All methods are @staticmethod.
    """

    @staticmethod
    def get_or_create(id: int, lang_code: str = "en", is_superuser: bool = False, is_banned: bool = False) -> dict:
        """
        Create user or get user data.
        """
        return User.get_or_create(id, is_superuser, is_banned, lang_code)


    @staticmethod
    def change_lang(id: int, lang_code: str):
        """
        Change user language.
        """
        return User.change_lang(id, lang_code)


    @staticmethod
    def get_all(id: int) -> dict:
        """
        return all user data.
        """
        return User.all_data(id)
    

    @staticmethod
    def toggle_ban(user_id: int, is_banned: bool) -> None:
        """
        Change user status.
        """
        return User.status(user_id, is_banned)
    

    @staticmethod
    def retrieve_game(user_id: int, type: int) -> dict:
        """
        User results in one game.
        """
        return User.retrieve_game(user_id, type)
    

    @staticmethod
    def all_games(user_id: int) -> dict:
        """
        User results in all games.
        """
        return User.all_games(user_id)
    

class GameModel:
    """
    This model is for working with games.
    P.S: All methods are @staticmethod.
    """

    @staticmethod
    def create(player_1: int, player_2: int, result: str, type: int, mid: str) -> dict:
        """
        return the number of shared games and more details.
        Result: player_1 | player_2 | draw
        """
        return Game.geme_add(player_1, player_2, type, result, mid)
        

class SponserModel:
    """
    Don't you want a doc string for this too? Stupid.
    """

    @staticmethod
    def get(id: int) -> dict:
        """
        return Sponser details.
        """
        return Sponser.retrieve(id)
    

    @staticmethod
    def get_all() -> list:
        """
        return all sponsers. A list of dictionaries.
        """
        return Sponser.get_all()
    

    @staticmethod
    def increase_member(id: int, number: int = 1) -> dict:
        """
        Increase in members joined for a sponsor.
        """
        return Sponser.increase_member(id, number)
