from django.contrib.auth.models import User
from django.db import models

from django.contrib.auth.models import AbstractUser

class Admin(AbstractUser):

    REQUIRED_FIELDS = []
    
    class Meta:
        verbose_name = "Admin"
        verbose_name_plural = "Admins"


class User(models.Model):
    id = models.BigIntegerField(primary_key=True)
    join_time = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)


    @classmethod
    def create_user(cls, id, is_admin):
        if is_admin:
            cls.objects.create(
                id=id,
                is_admin=True
            )
            return True
        
        cls.objects.create(
            id=id,
            is_admin=False
        )
        return True
        
        
    @classmethod
    def is_user(cls, id):
        try:
            cls.objects.get(id=id)
            return True
        except:
            return False
        

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


class Command(models.Model):
    command = models.CharField(max_length=256, primary_key=True)
    value = models.CharField(max_length=580)
