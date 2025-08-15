from django.db import models

from django.contrib.auth.models import AbstractUser

class Admin(AbstractUser):

    REQUIRED_FIELDS = []
    
    class Meta:
        verbose_name = "Admin"
        verbose_name_plural = "Admins"


class User(models.Model):
    id = models.BigIntegerField(primary_key=True)
    joined_time = models.DateTimeField(auto_now_add=True)
    is_superuser = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)


    @staticmethod
    def get_or_create_user(id):
        try:
            ins = User.objects.create(
                id=id,
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
    def get_all_user_data(id):
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
        

    @classmethod
    def is_admin(cls, id):
        try:
            cls.objects.get(id=id, is_admin=True)
            return True
        except:
            return False


class Game(models.Model):
    WINNER_CHOICES = [
        ('player_1', 'player_1'),
        ('player_2', 'player_2'),
        ('draw', 'Draw'),
    ]

    player_1 = models.ForeignKey(User, related_name="player_1", on_delete=models.CASCADE, null=True)
    player_2 = models.ForeignKey(User, related_name="player_2", on_delete=models.CASCADE, null=True)
    type = models.IntegerField()
    
    result = models.CharField(max_length=10, choices=WINNER_CHOICES)


class Score(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="score")
    games = models.IntegerField()
    wins = models.IntegerField()
    losses = models.IntegerField()


class Command(models.Model):
    command = models.CharField(max_length=256, primary_key=True)
    value = models.CharField(max_length=580)


    @classmethod
    def crate_command(cls, command, value):
        try:
            ins = cls.objects.get(command=command)
            raise Exception("commnad is existing")
        except:
            cls.objects.create(
                command=command,
                value=value
            )
            return True


    @classmethod
    def change_command_value(cls, command, value):
        try:
            cmd = cls.objects.get(command=command)
        except:
            raise Exception("commad in not exist")
        
        cmd.value = value
        cmd.save()
