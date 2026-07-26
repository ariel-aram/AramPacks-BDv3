from typing import override

from django.db import models


class MuseumCard(models.Model):
    user_id = models.BigIntegerField()
    card_id = models.CharField(max_length=64)
    position = models.IntegerField()

    class Meta:
        db_table = "museumcard"
        unique_together = [("user_id", "position")]
        ordering = ["user_id", "position"]

    @override
    def __str__(self):
        return f"MuseumCard(user={self.user_id}, pos={self.position})"
