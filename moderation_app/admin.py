from django.contrib import admin

from .models import Warning


@admin.register(Warning)
class WarningAdmin(admin.ModelAdmin):
    list_display = ("user_id", "guild_id", "moderator_id", "reason", "created_at")
    list_filter = ("guild_id",)
    search_fields = ("user_id", "reason")
    readonly_fields = ("created_at",)
