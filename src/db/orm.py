import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from app.models import User, Score



class UserStats:

    @staticmethod
    def get_or_create(id: int, is_superuser: bool = False, is_banned: bool = False) -> dict:
        try:
            ins = User.objects.get(id=id)
        except:
            ins = User.create(
                id=id,
                is_superuser=is_superuser,
                is_banned=is_banned,
            )
        return {
            "id": ins.id,
            "is_banned": ins.is_banned,
            "is_superuser": ins.is_superuser,
            "joined_time": ins.joined_time, 
        }


    @staticmethod
    def get_all(id: int) -> dict:
        context = User.all_data(id=id)
        return {
        "id": context["user"].id,
        "is_banned": context["user"].is_banned,
        "is_superuser": context["user"].is_superuser,
        "joined_time": context["user"].joined_time,
        "user_stats": {
                "wins": context["score"].wins,
                "losses": context["score"].losses,
                "games": context["score"].games,
            }
        }
        