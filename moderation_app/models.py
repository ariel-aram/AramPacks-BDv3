from django.db import models


class Warning(models.Model):
    guild_id = models.BigIntegerField()
    user_id = models.BigIntegerField()
    moderator_id = models.BigIntegerField()
    reason = models.TextField(default="No reason provided.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["guild_id", "user_id"]),
        ]

    def __str__(self):
        return f"Warning(guild={self.guild_id}, user={self.user_id}, reason={self.reason!r})"
