from django.db import models


class SpecialSpawnConfig(models.Model):
    guild_id = models.BigIntegerField(unique=True)
    special_channel = models.BigIntegerField(null=True)

    class Meta:
        db_table = "specialspawnconfig"
