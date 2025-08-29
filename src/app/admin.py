from django.contrib.admin import register
from django.contrib import admin

from app.models import  User, Game, Score, Admin, Sponser


@register(Admin)
class AdminAdmin(admin.ModelAdmin):
    list_display = ("username", "password")


@register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "is_superuser", "is_banned", "joined_time", "lang_code")


@register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("result", "player_1", "player_2", "type", "mid", "played_time")


@register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ("user", "wins", "games")


# @register(LocalizedText)
# class LocalizedTextAdmin(admin.ModelAdmin):
#     list_display = ("lang_code", "key", "value")


@register(Sponser)
class SponserAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "link", "joined_memebers", "is_active")