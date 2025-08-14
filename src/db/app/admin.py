from django.contrib.admin import register
from django.contrib import admin

from app.models import User


@register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "is_superuser", "is_banned", "joined_time")