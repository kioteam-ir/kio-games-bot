from .models import Game, Score

from django.dispatch import receiver
from django.db.models.signals import post_save


@receiver(post_save, sender=Game)
def add_score(sender, instance, created, **kwargs):
    if created:
        if instance.result == "player_2":
            Score.loser(instance.player_1, instance.type)
            Score.winner(instance.player_2, instance.type)
        elif instance.result == "player_1":
            Score.winner(instance.player_1, instance.type)
            Score.loser(instance.player_2, instance.type)
        else:
            Score.draw(instance.player_1, instance.type)
            Score.draw(instance.player_2, instance.type)