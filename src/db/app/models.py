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
    def create(id, is_superuser=False, is_banned=False):
        instance = User.objects.create(
            id=id,
            is_superuser=is_superuser,
            is_banned=is_banned,            
        )
        Score.objects.create(
            user=instance
        )
        return instance
    

    @staticmethod
    def all_data(id):
        user = User.objects.get(id=id)
        score = Score.objects.get(user=user)
        context = {
            "user": user,
            "score": score
        }
        return context


    def __str__(self):
        return f"{self.id}"


class Game(models.Model):
    WINNER_CHOICES = [
        ('player_1', 'player_1'),
        ('player_2', 'player_2'),
        ('draw', 'Draw'),
    ]
    mid = models.CharField(max_length=48)
    player_1 = models.ForeignKey(User, related_name="player_1", on_delete=models.CASCADE, null=True)
    player_2 = models.ForeignKey(User, related_name="player_2", on_delete=models.CASCADE, null=True)
    type = models.IntegerField()
    result = models.CharField(max_length=10, choices=WINNER_CHOICES)


    @staticmethod
    def geme_add(player_1, player_2, type, result):
        instance = Game.objects.create(
            player_1=User.objects.get(id=player_1),
            player_2=User.objects.get(id=player_2),
            type=type,
            result=result
        )
        return Game.score_handler(player_1, player_2, result)
    

    classmethod
    def score_handler(player_1, player_2, result):
        if result == "player_2":
            Score.loser(player_1)
            Score.winner(player_2)
            return True
        elif result == "player_1":
            Score.winner(player_1)
            Score.loser(player_2)
            return True
        else:
            Score.draw(player_1)
            Score.draw(player_2)
            return True


class Score(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="score")
    games = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)


    @staticmethod
    def winner(user_id):
        instance = Score.objects.get(user=user_id)
        instance.games += 1
        instance.wins += 1
        instance.save()


    @staticmethod
    def loser(user_id):
        instance = Score.objects.get(user=user_id)
        instance.games += 1
        instance.losses += 1
        instance.save()

    
    @staticmethod
    def draw(user_id):
        instance = Score.objects.get(user=user_id)
        instance.games += 1
        instance.save()


class LocalizedText(models.Model):
    key = models.IntegerField(primary_key=True)
    value = models.TextField(max_length=256)
    lang_code = models.CharField(max_length=2)