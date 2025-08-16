import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from orm import GameModel


def create_user():
    id = int(input("id: "))
    user = GameModel.create(1, 2, "draw", 1,"test")
    return user

print(create_user())
