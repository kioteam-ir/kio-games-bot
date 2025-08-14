import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from app.models import User



def create_user():
    id = 14949
    is_superuser = True
    User.create_user(id=id)

create_user()