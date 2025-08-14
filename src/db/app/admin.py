from django.contrib.admin import register
from django.contrib import admin

from app.models import User, Command, Game, Score, Admin


@register(Admin)
class AdminAdmin(admin.ModelAdmin):
    list_display = ("username", "password")

@register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "is_superuser", "is_banned", "joined_time")


@register(Command)
class CommandAdmin(admin.ModelAdmin):
    list_display = ("command", "value")


@register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("result", "player_1", "player_2", "type")


@register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ("user", "wins", "games")