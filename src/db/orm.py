import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from app.models import User



def create_user():
    id = int(input("id: "))
    is_superuser = True
    return User.get_all_user_data(id=id)

print(create_user())