from typing import override

from django.db import models


class FlexData(models.Model):
    user_id = models.BigIntegerField(unique=True)
    last_flex = models.BigIntegerField(default=0)

    class Meta:
        db_table = "flexdata"

    @override
    def __str__(self):
        return f"FlexData(user={self.user_id})"


class FlexGuildConfig(models.Model):
    guild_id = models.BigIntegerField(unique=True)
    mod_approval_channel_id = models.BigIntegerField(null=True, blank=True)
    public_flex_channel_id = models.BigIntegerField(null=True, blank=True)
    enabled = models.BooleanField(default=False)

    class Meta:
        db_table = "flex_guild_config"

    @override
    def __str__(self):
        return f"FlexGuildConfig(guild={self.guild_id}, enabled={self.enabled})"
