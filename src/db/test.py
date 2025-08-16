import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from orm import UserStats



def create_user():
    id = int(input("id: "))
    user = UserStats.get_all(id=id)
    return user

print(create_user())
