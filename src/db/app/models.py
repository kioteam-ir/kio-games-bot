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
    

    # @property
    # def is_admin(self):
    #     return True if User.objects.get(id=self.id).is_superuser == True else False
        
    
    def __str__(self):
        return f"{self.id}"


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
