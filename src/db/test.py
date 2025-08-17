import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from app.models import LocalizedText
from orm import GameModel, UserStats


def create_user():
    id = int(input("id: "))
    user = GameModel.create(1, 2, "draw", 1,"test")
    return user


def get_text(lang_code: str = "en"): return LocalizedText.get_text(lang_code)


def status():
    return UserStats.toggle_ban(1, False)

print(status())
