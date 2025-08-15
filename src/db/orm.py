import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from app.models import User, Score



class UserStats:

    @staticmethod
    def get_or_create(id: int, is_admin: bool = False, is_banned: bool = False) -> dict:
        try:
            ins = User.objects.create(
                id=id,
                is_admin=is_admin,
                is_banned=is_banned,
            )
        except:
            ins = User.objects.get(id=id)
        finally:
            return {
                "id": ins.id,
                "is_banned": ins.is_banned,
                "is_superuser": ins.is_superuser,
                "joined_time": ins.joined_time, 
            }
        

    @staticmethod
    def get_all(id: int) -> dict:
        user = User.objects.get(id=id)
        score = Score.objects.get(user=user)
        return {
            "id": user.id,
            "is_banned": user.is_banned,
            "is_superuser": user.is_superuser,
            "joined_time": user.joined_time,
            "user_stats": {
                    "wins": score.wins,
                    "losses": score.losses,
                    "games": score.games,
                }
            }
        