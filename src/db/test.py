import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from app.models import LocalizedText
from orm import GameModel, UserStats


def create_user():
    id = int(input("id: "))
    user = UserStats.get_or_create(31, True, False, "en")
    return user


def get_text(lang_code: str = "en"): return LocalizedText.get_text(lang_code)


def status():
    return UserStats.toggle_ban(1, False)


def all_data():
    return UserStats.get_all(31)

print(all_data())
