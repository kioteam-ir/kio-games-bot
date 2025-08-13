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


class Game(models.Model):
    winner = models.ForeignKey(User, related_name="winner", on_delete=models.CASCADE)
    loser = models.ForeignKey(User, related_name="loser", on_delete=models.CASCADE)
    type = models.IntegerField()


class Score(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="score")
    games = models.IntegerField()
    wins = models.IntegerField()
    