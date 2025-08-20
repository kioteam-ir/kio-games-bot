from django.db import models
from django.db.models import Q

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
    lang_code = models.CharField(max_length=2)
    

    @staticmethod
    def get_or_create(id: int, is_superuser: bool = False, is_banned: bool = False, lang_code: str = "fa"):
        try:
            ins = User.objects.get(id=id)
        except:
            ins = User.create(
                id,
                is_superuser,
                is_banned,
                lang_code
            )
        return {
            "id": ins.id,
            "is_banned": ins.is_banned,
            "is_superuser": ins.is_superuser,
            "joined_time": ins.joined_time,
            "lang_code": lang_code
        }
    
    @staticmethod
    def create(id, is_superuser=False, is_banned=False, lang_code="fa"):
        instance = User.objects.create(
            id=id,
            is_superuser=is_superuser,
            is_banned=is_banned,
            lang_code=lang_code,
        )
        return instance
    

    @staticmethod
    def all_data(id):
        user = User.objects.get(id=id)
        score = Score.objects.get(user=user)
        return  {
            "id": user.id,
            "is_banned": user.is_banned,
            "is_superuser": user.is_superuser,
            "joined_time": user.joined_time,
            "lang_code": user.lang_code,
            "games_stats": {
                "games": score.games,
                "wins": score.wins,
                "losses": score.losses,
            }
        }


    def __str__(self):
        return f"{self.id}"
    

    @classmethod
    def status(cls, user_id, is_banned):
        user = cls.objects.get(id=user_id)
        user.is_banned = is_banned
        user.save()

    
    @staticmethod
    def retrieve_game(id, type):
        context = Score.objects.get(user=id, game_type=type)
        return {
            "total": context.games,
            "wins": context.wins,
            "draws": context.games - (context.wins + context.losses),
            "losses": context.losses,
        }


    @staticmethod
    def all_games(id):
        list_data = []
        context = Score.objects.filter(user=id).values("games", "wins", "game_type", "losses")
        for row in context:
            list_data.append(row)
        return list_data


class Game(models.Model):
    WINNER_CHOICES = [
        ('player_1', 'player_1'),
        ('player_2', 'player_2'),
        ('draw', 'draw'),
    ]
    mid = models.CharField(max_length=48)
    player_1 = models.ForeignKey(User, related_name="player_1", on_delete=models.CASCADE, null=True)
    player_2 = models.ForeignKey(User, related_name="player_2", on_delete=models.CASCADE, null=True)
    type = models.IntegerField()
    result = models.CharField(max_length=10, choices=WINNER_CHOICES)
    played_time =  models.DateTimeField(auto_now_add=True)


    @classmethod
    def geme_add(cls, player_1, player_2, type, result, mid):
        instance = cls.objects.create(
            player_1=User.objects.get(id=player_1),
            player_2=User.objects.get(id=player_2),
            type=type,
            result=result,
            mid=mid
        )
        cls.score_handler(instance)
        return cls.shared_game(instance)
    

    @staticmethod
    def shared_game(instance):
        games = Game.objects.filter(type=instance.type).filter(
            Q(player_1=instance.player_1) | Q(player_1=instance.player_2)
            ).filter(
            Q(player_2=instance.player_2) | Q(player_2=instance.player_1)
            )
        return {
            "total": games.count(),
            "p1_wins": games.filter(result="player_1").count(),
            "p2_wins": games.filter(result="player_2").count(),
            "draws": games.filter(result="draw").count(),
        }
    

    @staticmethod
    def score_handler(instance):
        if instance.result == "player_2":
            Score.loser(instance.player_1, instance.type)
            Score.winner(instance.player_2, instance.type)
            return True
        elif instance.result == "player_1":
            Score.winner(instance.player_1, instance.type)
            Score.loser(instance.player_2, instance.type)
            return True
        else:
            Score.draw(instance.player_1, instance.type)
            Score.draw(instance.player_2, instance.type)
            return True


class Score(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="score")
    games = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    game_type = models.IntegerField(default=1)


    @staticmethod
    def winner(user_id, type):
        try:
            instance = Score.objects.get(user=user_id, game_type=type)
        except:
            instance = Score.objects.create(user=user_id, game_type=type)
        instance.games += 1
        instance.wins += 1
        instance.save()


    @staticmethod
    def loser(user_id, type):
        try:
            instance = Score.objects.get(user=user_id, game_type=type)
        except:
            instance = Score.objects.create(user=user_id, game_type=type)
        instance.games += 1
        instance.losses += 1
        instance.save()

    
    @staticmethod
    def draw(user_id, type):
        try:
            instance = Score.objects.get(user=user_id, game_type=type)
        except:
            instance = Score.objects.create(user=user_id, game_type=type)
        instance.games += 1
        instance.save()

    



class LocalizedText(models.Model):
    key = models.IntegerField()
    value = models.TextField(max_length=256)
    lang_code = models.CharField(max_length=2, default="fa")

    @staticmethod
    def get_text(lang_code):
        text_list = []
        instance = LocalizedText.objects.filter(lang_code=lang_code).values("key", "value")
        for row in instance:
            text_list.append(row)
        return text_list
    